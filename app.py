import os
import zipfile

from flask import Flask, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_dropzone import Dropzone

from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@db:5432/image_database',
    UPLOADED_PATH=os.path.join(basedir, 'tmp/jp2/'),
    CONVERTED_PATH=os.path.join(basedir, 'tmp/converted/'),
    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_CUSTOM=True,
    DROPZONE_ALLOWED_FILE_TYPE='.jp2',
    DROPZONE_MAX_FILE_SIZE=2048,  # set max size limit to a large number, here is 1024 MB
    DROPZONE_MAX_FILES=30,
    DROPZONE_IN_FORM=True,
    DROPZONE_UPLOAD_ON_CLICK=True,
    DROPZONE_UPLOAD_ACTION='handle_upload',  # URL or endpoint
    DROPZONE_UPLOAD_BTN_ID='submit',
)
db = SQLAlchemy(app)
dropzone = Dropzone(app)

class Batch(db.Model):
    __tablename__ = "batch"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    path = db.Column(db.String(64), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    children = db.relationship("Image")

class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    size = db.Column(db.Integer, nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'))
    
    
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        #shutil.make_archive('batch/' + title, 'zip', os.path.join(basedir, 'tmp2'))
        archives = Batch.query.order_by(Batch.date_created).all()
        return render_template('index.html', files=archives)
    else:    
        #archives = os.listdir('batch/')
        archives = Batch.query.order_by(Batch.date_created).all()
        return render_template('index.html', files=archives)


@app.route('/upload', methods=['POST'])
def handle_upload():
    if request.method == 'POST':
        for key, f in request.files.items():
            if key.startswith('file'):
                f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
                from_file = os.path.join(app.config['UPLOADED_PATH'], f.filename)
                filename = os.path.splitext(f.filename)[0]
                to_file = os.path.join(basedir, 'tmp') + '/converted/' + filename + '.tif'
                try:
                    if os.system('vips copy ' + from_file + ' ' + to_file) != 0:
                        raise Exception('Command vips did not work!')
                except:
                    os.system('opj_decompress -i ' + from_file + ' -o ' + to_file)
                    print("Command opj_decompress does not work")   
        title = request.form.get('title')
        zip_path = os.path.join(basedir, 'batch/'+title+'.zip')
        zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        path = os.path.join(basedir, 'tmp/converted/')
        for root, dirs, files in os.walk(path):
            for file in files:
                zipf.write( os.path.join(root, file),
                            os.path.relpath(os.path.join(root, file), path))
        zipf.close()
        for file in os.listdir(app.config['UPLOADED_PATH']):
            os.remove(app.config['UPLOADED_PATH'] + file)
        for file in os.listdir(app.config['CONVERTED_PATH']):
            os.remove(app.config['CONVERTED_PATH'] + file)  
        filenames = os.listdir('batch/')
        zip_name = title + '.zip'
        new_zip = Batch(name=zip_name, path=zip_path)
        try:
            db.session.add(new_zip)
            db.session.commit()
            archives = Batch.query.order_by(Batch.date_created).all()
            return render_template('index.html', files=archives)
        except:
            return 'Error during db insertion', 500
    else:
        return '', 204

@app.route('/batch/<path:filename>', methods=['GET', 'POST'])
def log(filename):
    return send_from_directory(
        os.path.abspath('batch'),
        filename,
        as_attachment=True
    )

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def log2(filename):
    return send_from_directory(
        os.path.abspath('tmp2'),
        filename,
        as_attachment=True
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)