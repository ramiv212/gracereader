import os
from flask import Flask, flash, request, redirect, url_for,render_template,send_file
from werkzeug.utils import secure_filename
from gracereader import process_as_image_or_pdf,create_pdf_po_document
import json

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}

# TODO refactor the date finding logic
# TODO make sure all HTML field names match PDF field names
# TODO fix all frontend and backend validation
# TODO move labels for radio buttons to after radio
# TODO name the file something different when exporting, delete after download
# TODO add validation when button is pushed without a selected file
# TODO add image to pdf download
# TODO fill in name based on amex number
# TODO test each dropdown option

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
    