from flask import Flask, request,render_template,send_file
from grace_reader import process_as_image_or_pdf,create_pdf_po_document,send_as_stream_and_delete


UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}

# TODO refactor the date finding logic
# TODO test a pdf receipt with many pages
# TODO add valiation for adding a signature when someone writes in a name that does not exist
# TODO make ordered_by be a dropdown??
# TODO fixed dropdowns dont render the first time render button is pushed
# TODO PDF render to PO is now broken

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route("/", methods=['GET', 'POST'])
    def hello_world():
        
        def file_was_uploaded(f):
            print(f)
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
        
                
            

    @app.route("/renderform", methods=['GET', 'POST'])
    def render_form():

        if request.method == 'POST':
            new_filename =  create_pdf_po_document(request.form)
            path = f"static/final/{new_filename}.pdf"
            cache = send_as_stream_and_delete(path)
            return send_file(cache, as_attachment=True, download_name=f"{new_filename}.pdf")
        
        elif request.method == 'GET':
            return render_template('index.html', response_object = {}, title="TITLE")
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
