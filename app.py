from distutils import archive_util
import sys
import os
import zipfile

from subprocess import check_output, CalledProcessError, STDOUT
from flask import Flask, request, render_template, send_from_directory, redirect, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dataclasses import dataclass


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@db:5432/image_database',
    UPLOADED_PATH=os.path.join(basedir, 'tmp/jp2/'),
    CONVERTED_PATH=os.path.join(basedir, 'tmp/converted/'),
)
db = SQLAlchemy(app)

ROWS_PER_PAGE = 8

@dataclass
class Batch(db.Model):
    id: int
    name: str
    path: str
    date_created: str
    state: str

    __tablename__ = "batch"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    path = db.Column(db.String(64), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.now)
    state = db.Column('state', db.Enum('waiting', 'exists', 'removed', 'failed', name='state'), nullable=False)
    children = db.relationship("Image")

class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    exit_code = db.Column(db.Integer, nullable=False)
    imsize = db.Column(db.Integer, nullable=True)
    resources = db.Column(db.String(32), nullable=True)
    command = db.Column('command', db.Enum('vips', 'openjpeg', name='command'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'))
    
@app.route('/', methods=['POST', 'GET'])
def index():
    return redirect('/home')
    
@app.route('/home', methods=['POST', 'GET'])
def home():
    page = request.args.get('page', 1, type=int)
    archives = Batch.query.order_by(db.desc(Batch.date_created)).filter((Batch.state == 'exists') | (Batch.state == 'waiting')).paginate(page=page, per_page=ROWS_PER_PAGE)
    return render_template('index.html', archives=archives)

@app.route("/api/table", methods=['GET', 'POST'])
def table():
    page = request.args.get('page', 1, type=int)
    archives = Batch.query.order_by(db.desc(Batch.date_created)).filter((Batch.state == 'exists') | (Batch.state == 'waiting')).paginate(page=1, per_page=ROWS_PER_PAGE).items
    return jsonify(archives)

# adds batch to database wit id
@app.route("/add_batch", methods=['GET', 'POST'])
def result_json():
    if request.method == 'POST':
        #check if archive name exists
        recv_data = request.json
        zip_name = str(recv_data['title'])+'.zip'
        exists = Batch.query.filter((Batch.name==zip_name) & (Batch.state=='exists')).scalar()
        if exists:
            return 'Tento název už existuje!', 500
        zip_path = os.path.join(basedir, 'batch/'+zip_name)
        new_zip = Batch(name=zip_name, path=zip_path, state='waiting')
        try:
            db.session.add(new_zip)
            db.session.flush()
            db.session.commit()
        except:
            return 'Error during db insertion', 500
    page = request.args.get('page', 1, type=int)
    archives = Batch.query.order_by(db.desc(Batch.date_created)).filter((Batch.state == 'exists') | (Batch.state == 'waiting')).paginate(page=1, per_page=ROWS_PER_PAGE).items
    return jsonify(archives)


@app.route('/upload', methods=['POST', 'GET'])
def handle_upload():
    if request.method == 'POST':
        title = request.form.get('title')
        zip_name = title+'.zip'
        searched = Batch.query.filter((Batch.name==zip_name) & (Batch.state=='waiting')).scalar()
        print(searched, file=sys.stderr)
        zipf = zipfile.ZipFile(searched.path, 'w', zipfile.ZIP_DEFLATED)
        for key, f in request.files.items():
            if key.startswith('file'):
                f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
                from_file = os.path.join(app.config['UPLOADED_PATH'], f.filename)
                jp2_size = os.path.getsize(from_file)/1000000
                filename = os.path.splitext(f.filename)[0]
                to_file = os.path.join(basedir, 'tmp') + '/converted/' + filename + '.tif'
                try:
                    cmd = '/usr/bin/time -f %M:%e vips copy ' + from_file + ' ' + to_file + ' 2>&1 >/dev/null'
                    out = check_output(cmd, shell=True)
                    resources = out.decode("utf-8")
                    new_image = Image(name=filename, exit_code=0, command='vips', batch_id=searched.id, resources=resources, imsize=jp2_size)
                    try:
                        db.session.add(new_image)
                        db.session.commit()
                    except:
                        return 'Error during db insertion (Image table, line 96)', 500
                except CalledProcessError as e:
                    print(e.returncode, e.output)
                    try:
                        cmd = '/usr/bin/time -f %M:%e opj_decompress -i ' + from_file + ' -o ' + to_file + ' 2>&1 >/dev/null'
                        out = check_output(cmd, shell=True)
                        resources = out.decode("utf-8")
                        new_image = Image(name=filename, exit_code=1, command='openjpeg', resources=resources, batch_id=searched.id, imsize=jp2_size)
                        try:
                            db.session.add(new_image)
                            db.session.commit()
                        except:
                            return 'Error during db insertion (Image table, line 106)', 500
                    except:
                        # both commands did not work, insert batch and image to database as failed
                        # insert image:
                        new_image = Image(name=filename, exit_code=2, batch_id=searched.id)
                        try:
                            db.session.add(new_image)
                            db.session.commit()
                        except:
                            return 'Error during db insertion (Image table, line 115)', 500
                        # change batch to failed state
                path = os.path.join(basedir, 'tmp/converted/')
                zipf.write(to_file)
                os.remove(from_file)
                os.remove(to_file)  
        zipf.close()
        # add successfull zip to database as batch
        current_batch = Batch.query.get_or_404(searched.id)
        try:
            current_batch.state = 'exists'
            db.session.commit()
            return redirect('/')
        except:
            return 'There was a problem with changing state from \'waiting\' to \'exists\''
    else:
        return '', 204

@app.route('/batch/<path:filename>', methods=['GET', 'POST'])
def log(filename):
    return send_from_directory(
        os.path.abspath('batch'),
        filename,
        as_attachment=True
    )

@app.route('/batch_records', methods=['GET'])
def batch_records():
    page = request.args.get('page', 1, type=int)
    batches = Batch.query.order_by(db.desc(Batch.id)).paginate(page=page, per_page=ROWS_PER_PAGE)
    return render_template('batch_records.html', archives=batches)

@app.route('/image_records', methods=['GET'])
def image_records():
    page = request.args.get('page', 1, type=int)
    images = Image.query.order_by(db.desc(Image.id)).paginate(page=page, per_page=ROWS_PER_PAGE)
    return render_template('image_records.html', images=images)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_batch(id):
    batch_to_delete = Batch.query.get_or_404(id)
    try:
        if os.path.isfile(batch_to_delete.path):
            os.remove(batch_to_delete.path)
        batch_to_delete.state = 'removed'
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting the file'



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)