import io, os, shutil
from fillpdf import fillpdfs
from PIL import Image
from pdf2image import convert_from_bytes
import PyPDF2
import re

from parse.validation import file_extension_is_image
from parse.parse import parse_image
from parse.serialize import serialize_form_object
from const import *


def send_as_stream_and_delete(path):
    cache = io.BytesIO()
    with open(path, 'rb') as fp:
        shutil.copyfileobj(fp, cache)
        cache.flush()
    cache.seek(0)
    os.remove(path)
    return cache



# if it is a new day, initialize all PO numbers to 1 for everyone
def check_if_new_day(today,DATE_OF_LAST_PO_GENERATION):
    if DATE_OF_LAST_PO_GENERATION < today:
        for person in PO_NUMBER_BY_PERSON:
            PO_NUMBER_BY_PERSON[person] = 1

    # Set today as the date of last PO generation
    DATE_OF_LAST_PO_GENERATION = date.today()


def add_receipt_to_pdf(receipt_image_or_pdf, count):
    print(f'ran add receipt count:{count}')
    path = os.path.join(os.getcwd(),f'static/PO{count}.pdf')
    current_pdf = PyPDF2.PdfReader(path)
    new_pdf = PyPDF2.PdfWriter()
    
    is_image, file_extension = file_extension_is_image(receipt_image_or_pdf)

    print(
        f"is image:{is_image}, type of {type(is_image)}",
        f"file extension:{file_extension}, type of {type(file_extension)}",
    )

    if is_image:
        convert_to_jpeg = Image.open(receipt_image_or_pdf).convert("RGB")
        converted_jpeg_path = os.path.join(os.getcwd(),f'static/receipt.jpg')
        convert_to_jpeg.save(converted_jpeg_path)

        print(f'ran image count:{count}')
        # create a blank page on the pdf and append the image to it, then export a new pdf
        new_pdf.add_page(current_pdf.pages[0])
        new_pdf.add_blank_page()

        count +=1
        path = os.path.join(os.getcwd(),f'static/PO{count}.pdf')
        path2 = os.path.join(os.getcwd(),f'static/PO{count + 1}.pdf')
        
        new_pdf.write(path)
        fillpdfs.place_image(converted_jpeg_path, 0, 0, path,
                             path2, 2, width=600, height=800)
        
        count += 1
        print(f"image receipt has been added, count is now {count}")
        return count

    elif not is_image and file_extension:
        print(f'ran is pdf count:{count}')
        # create a new pdf, append the po pdf page, then append the receipt pdf pages
        receipt_pdf = PyPDF2.PdfReader(receipt_image_or_pdf)
        new_pdf.add_page(current_pdf.pages[0])
        for page in receipt_pdf.pages:
            new_pdf.add_page(page)

        count += 1
        path = os.path.join(os.getcwd(),f'static/PO{count}.pdf')
        new_pdf.write(path)
        print(f"pdf receipt has been added, count is now {count}")
        return count


    # if no receipt image can be found, skip this step and rename the previous pdf in the pipeline
    # so as to not break teh process
    else:
        print(f'ran no file count:{count}')
        
        path = os.path.join(os.getcwd(),f'static/PO{count}.pdf')
        path2 = os.path.join(os.getcwd(),f'static/PO{count + 1}.pdf')

        os.rename(path,path2)
        count += 1
        print(f"no receipt has been added, count is now {count}")
        return count



def add_signature_to_po_pdf(ordered_by, count):
    print(f'ran add signature count:{count}')
    if len(ordered_by) > 0 and ordered_by in PO_NUMBER_BY_PERSON:
        path = os.path.join(os.getcwd(),f"static/signatures/{ordered_by}.png")

        fillpdfs.place_image(path,
            90,
            680, 
            f'static/PO{count}.pdf', f'static/PO{count + 1}.pdf', 1, width=150, height=100)
        count += 1

        return count
        
    # if there is no ordered_by, rename the previous pdf in the pipeline to the next
    # as if the step had completed so that the process does not break
    else:
        path = os.path.join(os.getcwd(),f'static/PO{count}.pdf')
        path2 = os.path.join(os.getcwd(),f'static/PO{count + 1}.pdf')
        os.rename(path,path2)
        count += 1
        return count

def delete_generated_receipt_files():
    list_of_files_in_static = os.listdir('static')

    regex_str = f"(PO[0-9]|receipt)"

    # Compile the regex pattern
    pattern = re.compile(regex_str)

    # Search for matches in the list
    matches = [s for s in list_of_files_in_static if pattern.search(s)]

    # Delete the receipt files that match the regex ("PO" followed by a single digit, OR a string of "receipt")
    for file in matches:
        os.remove(f"static/{file}")


# will look through the "static" folder for the "receipt" file an return it's extension
def get_receipt_file_extension():
    list_of_files_in_static = os.listdir('static')
    for file in list_of_files_in_static:
        if "receipt" in file:
            return file.split(".")[1]


def create_pdf_po_document(immutable_dict):
    print("RAN CREATE")
    # create an incrementing count for PO export
    count = 1
    input_pdf_path = os.path.join(os.getcwd(),"static/PO.pdf")

    ordered_by = immutable_dict['ORDERED BY']

    # name the new generated pdf by the PO number
    finalized_po_filename = immutable_dict['NUMBER']

    # check for if there is no submitted PO number
    # if not, generate one using today's date
    if len(finalized_po_filename) == 0:
        todays_date = date.today().strftime("%m%d")
        finalized_po_filename = f"PO{todays_date}01"

    receipt_file_extension = get_receipt_file_extension()

    print(serialize_form_object(immutable_dict))

    # fill in the blank PDF with information from form
    path = os.path.join(os.getcwd(),f"static/PO{count}.pdf")
    fillpdfs.write_fillable_pdf(
        input_pdf_path, path, serialize_form_object(immutable_dict))
    
    path2 = os.path.join(os.getcwd(),f'static/receipt.{receipt_file_extension}')
    count = add_receipt_to_pdf(path2,count)
    
    count = add_signature_to_po_pdf(ordered_by,count)

    # rename the final pdf of the pipeline to the generated PO number
    path3 = os.path.join(os.getcwd(),f'static/PO{count}.pdf')
    # print(os.listdir("static"))

    renamed_path = os.path.join(os.getcwd(),f"static/final/{finalized_po_filename}.pdf")

    os.rename(path3,renamed_path)

    # delete_generated_receipt_files()

    check_if_new_day(date.today(),DATE_OF_LAST_PO_GENERATION)

    # add one to the number of POs of this person
    if ordered_by in PO_NUMBER_BY_PERSON:
        PO_NUMBER_BY_PERSON[ordered_by] = PO_NUMBER_BY_PERSON[ordered_by] + 1

    return finalized_po_filename


def export_to_file_named_receipt(read_file, extension):
    path = os.path.join(os.getcwd(),f"static/receipt.{extension}")

    with open(path, "wb") as binary_file:
        # Write bytes to file
        binary_file.write(read_file)


def process_as_image_or_pdf(file):
    filename = file.filename
    read_file = file.read()

    is_image, extension = file_extension_is_image(filename)

    # create a file named "receipt" of the extension of the parent file
    export_to_file_named_receipt(read_file, extension)

    # if extension is image, create a new image with the name 'receipt' and the same extension
    if is_image:
        return parse_image(read_file)

    else:
        pdf_to_image = convert_from_bytes(read_file)[0]

        # img = Image.open(pdf_to_image, mode='r')

        img_byte_arr = io.BytesIO()
        pdf_to_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        return parse_image(img_byte_arr)
