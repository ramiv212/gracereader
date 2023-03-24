import os
from flask import Flask, flash, request, redirect, url_for,render_template,send_file
from werkzeug.utils import secure_filename
from gracereader import process_as_image_or_pdf,create_pdf_po_document
import json

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}


# TODO make sure all HTML field names match PDF field names
# TODO fix all frontend and backend validation
# TODO add a different name for each downloaded PO
# TODO remember the options you fill in for name, dept, account
# TODO get find AMEX and fill it in automatically if found
# TODO automatically get today's date
# TODO mobile version
# TODO move labels for radio buttons to after radio

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello_world():

    response_object = {}

    if request.method == 'POST':
        f = request.files.get('receipt')
        response_object = process_as_image_or_pdf(f)

    return render_template('index.html', response_object = response_object, title="TITLE")

@app.route("/renderform", methods=['POST'])
def render_form():

    create_pdf_po_document(request.form)

    path = "static/new.pdf"
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
    