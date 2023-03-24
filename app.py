import os
from flask import Flask, flash, request, redirect, url_for,render_template,send_file
from werkzeug.utils import secure_filename
from gracereader import parse_image
import json

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello_world():

    response_object = {}

    if request.method == 'POST':
        f = request.files.get('receipt')
        response_object = parse_image(f)

    return render_template('index.html', response_object = response_object, title="TITLE")

@app.route("/renderform", methods=['POST'])
def render_form():
    print(request.form)
    path = "static/new.pdf"
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)