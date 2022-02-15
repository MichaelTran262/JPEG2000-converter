import os

from flask import Flask, request, render_template, send_from_directory
from flask_dropzone import Dropzone
import shutil

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config.update(
    UPLOADED_PATH=os.path.join(basedir, 'tmp'),
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

dropzone = Dropzone(app)

@app.route('/')
def index():
    filenames = os.listdir('tmp2/')
    return render_template('index.html', files=filenames)


@app.route('/upload', methods=['POST'])
def handle_upload():
    if request.method == 'POST':
        title = request.form.get('title')
        for key, f in request.files.items():
            if key.startswith('file'):
                f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
                from_file = os.path.join(app.config['UPLOADED_PATH'], f.filename)
                filename = os.path.splitext(f.filename)[0]
                to_file = os.path.join(basedir, 'tmp2') + '/' + filename + '.tif'
                try:
                    if os.system('vips copy ' + from_file + ' ' + to_file) != 0:
                        raise Exception('Libs did not work')
                except:
                    os.system('opj_decompress -i ' + from_file + ' -o ' + to_file)
                    print("command does not work")
    return '', 204

@app.route('/', methods=['POST'])
def handle_form():
    title = request.form.get('title')
    #shutil.make_archive('batch/' + title, 'zip', os.path.join(basedir, 'tmp2'))
    filenames = os.listdir('tmp2/')
    return render_template('index.html', files=filenames)

@app.route('/tmp2/<path:filename>', methods=['GET', 'POST'])
def log(filename):
    return send_from_directory(
        os.path.abspath('tmp2'),
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)