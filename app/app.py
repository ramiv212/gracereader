import os
from flask import Flask, flash, request, redirect, url_for,render_template,send_file
from werkzeug.utils import secure_filename
from grace_reader import process_as_image_or_pdf,create_pdf_po_document,send_as_stream_and_delete
import json


UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}

# TODO refactor the date finding logic
# TODO make sure all HTML field names match PDF field names
# TODO fix all frontend and backend validation
# TODO name the file something different when exporting, delete after download
# TODO add validation when button is pushed without a selected file
# TODO test each dropdown option
# TODO test a pdf receipt with many pages
# TODO overwrite auto generated PO number,date,requested by if there is one in the 'NUMBER' field
# TODO add valiation for adding a signature when someone writes in a name that does not exist
# TODO make ordered by a dropdown??


def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route("/", methods=['GET', 'POST'])
    def hello_world():
        
        def file_was_uploaded(f):
            if f:
                response_object = process_as_image_or_pdf(f)
                return render_template('index.html', response_object = response_object)
            else: 
                return render_template('index.html', response_object = {
                    'no_file': True,
                }, 
            )
        
        if request.method == 'POST':
            f = request.files.get('receipt')
            return file_was_uploaded(f)
        else:
            return render_template('index.html', response_object = {}, title="TITLE")
        
                
            

    @app.route("/renderform", methods=['POST'])
    def render_form():

        new_filename =  create_pdf_po_document(request.form)

        path = f"app/static/final/{new_filename}.pdf"

        cache = send_as_stream_and_delete(path)

        return send_file(cache, as_attachment=True, download_name=f"{new_filename}.pdf")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
