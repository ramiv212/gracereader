import io, os, shutil
import pytesseract
import cv2
from dateutil.parser import parse
import numpy as np
import pyap
from fillpdf import fillpdfs
import PyPDF2
from datetime import date
import re
from PIL import Image,ImageOps

VENDOR_NAMES = ['amazon', 'walmart']

CARD_TO_NAME_DICT = {
    '2149': 'Johny Hernandez'
}

VENDOR_TO_DEPT_DICT = {

}

VENDOR_TO_ACCT_DICT = {

}

PO_NUMBER_BY_PERSON = {
    'Johny Hernandez': 1
}

DATE_OF_LAST_PO_GENERATION = date.today()

def send_as_stream_and_delete(path):
    cache = io.BytesIO()
    with open(path, 'rb') as fp:
        shutil.copyfileobj(fp, cache)
        cache.flush()
    cache.seek(0)
    os.remove(path)
    return cache


def file_extension_is_image(filename):
    file_extension = filename.split(".")[1]

    if file_extension == "png" or file_extension == "jpg" or file_extension == "jpeg" or file_extension == "webp":
        print(file_extension)
        return True, file_extension
    elif file_extension == "pdf":
        return False, file_extension
    else:
        return False,None


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def find_addresses(full_text_array):
    # parse the image text as one big blob and
    fulltext = " ".join(full_text_array)
    return pyap.parse(fulltext, country='US')


def string_includes_month(string):
    months_array = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]
    if any(ext in string for ext in months_array):
        return string


def find_date(text_line):
    non_slash_date_array = []

    # check if there is a slash in the text line
    if "/" in text_line and is_date(text_line):
        if " " in text_line:
            split_date = text_line.split()
            for sub_item in split_date:
                if "/" in sub_item:
                    return sub_item
            else:
                return sub_item

    # check if it's amazon-style date "March 15, 2023"
    if string_includes_month(text_line) and "," in text_line and "shipped" not in text_line.lower() and "transactions" not in text_line:
        non_slash_date_array.clear()
        non_slash_date_string = ""
        text_line_no_comma = text_line.replace(',', '')
        split_date = text_line_no_comma.split()

        for sub_item in split_date:
            if string_includes_month(sub_item) or sub_item.isnumeric():
                non_slash_date_array.append(sub_item)
                non_slash_date_string = " ".join(non_slash_date_array)

        return non_slash_date_string


# basically just looks for the highest float it can find in the text blob
# not very sophisticated right now
def find_total(text_line, max_total_list):
    split_sub_item = text_line.split()
    for sub_item in split_sub_item:
        if (sub_item[0].isnumeric() or sub_item[0] == "$") and sub_item[-1].isnumeric() and "." in sub_item:
            max_total_list.append(float(sub_item.strip("$")))


def find_card_digits(text_line):
    if "****" in text_line or "last digits" in text_line.lower() or "XXXX" in text_line or "debit" in text_line.lower() or "xxx" in text_line:
        string_without_letter_o_or_spaces = text_line.lower().replace("o",
                                                                      "0").replace(" ", "")

        matches = re.findall(r"\d{3,4}", string_without_letter_o_or_spaces)
        if matches:
            return matches


def find_requested_by(card_digits):
    if card_digits in CARD_TO_NAME_DICT:
        return CARD_TO_NAME_DICT[card_digits]
    else:
        return ""


def find_amex_purchase(text_line):
    if "amex" in text_line.lower() or "american express" in text_line.lower():
        return True


def find_vendors(text_line):
    # if vendor name is in the text line
    if any(ext in text_line.lower() for ext in VENDOR_NAMES):
        split_text_line = text_line.split(" ")
        for sub_text_item in split_text_line:
            for vendor in VENDOR_NAMES:
                if vendor in sub_text_item.lower():
                    return vendor.capitalize()

# if it is a new day, initialize all PO numbers to 1 for everyone
def check_if_new_day(today,DATE_OF_LAST_PO_GENERATION):
    if DATE_OF_LAST_PO_GENERATION < today:
        for person in PO_NUMBER_BY_PERSON:
            PO_NUMBER_BY_PERSON[person] = 1

    # Set today as the date of last PO generation
    DATE_OF_LAST_PO_GENERATION = date.today()


def generate_po_number(ordered_by):
    if ordered_by:
        split_name = ordered_by.split(" ")
        first_initial = split_name[0][0].upper()
        second_initial = split_name[1][0].upper()

        todays_date = date.today()
        todays_date_as_str = todays_date.strftime("%m%d")

        po_number = PO_NUMBER_BY_PERSON[ordered_by]
        po_number_as_two_digits = f"{po_number:02}"

        return f"{first_initial}{second_initial}{todays_date_as_str}{po_number_as_two_digits}"
    
    else:
        return ""


def serialize_parsed_text(image_text):
    full_text_array = image_text.splitlines()
    addresses = find_addresses(full_text_array)
    receipt_date = ""
    max_total_list = []
    is_amex_purchase = False
    vendor_name = ""
    requested_by = ""
    number = ""

    if 'TOTAL' in image_text or 'DEBIT' in image_text or 'Total' in image_text:
        for text_line in full_text_array:
            if text_line != "":
                find_total(text_line, max_total_list)

                if find_amex_purchase(text_line):
                    is_amex_purchase = True

                # fix this later. It returns none because this is being searched for overe every line of text
                if not find_date(text_line) == None:
                    receipt_date = find_date(text_line)

                if find_vendors(text_line):
                    vendor_name = find_vendors(text_line)

                card_digits = find_card_digits(text_line)
                if card_digits and len(card_digits) == 1:
                    requested_by = find_requested_by(card_digits[0])

                if not (requested_by == ""):
                    number = generate_po_number(requested_by)
                

        if not addresses:
            return {
                "NUMBER": number,
                "VENDOR NAME": vendor_name,
                "ORDERED BY": requested_by,
                "Date2_af_date": receipt_date,
                "Text1": max(max_total_list),
                "Check Box10": is_amex_purchase,
            }
        else:
            return {
                "VENDOR NAME": vendor_name,
                "ORDERED BY": requested_by,
                "ADDRESS": addresses[0].as_dict()['full_street'],
                "CITY": addresses[0].as_dict()['city'],
                "STATE": addresses[0].as_dict()['region1'],
                "ZIP": addresses[0].as_dict()['postal_code'],
                "Date1_af_date": date.today().strftime("%m/%d/%y"),
                "Date2_af_date": receipt_date,
                "Text1": max(max_total_list),
                "Check Box10": is_amex_purchase,
            }


def parse_image(image_file):
    # each text string will be appended to this list to be serialized later
    text_list = ""

    # Read image from which text needs to be extracted
    bytes_as_np_array = np.frombuffer(image_file, dtype=np.uint8)
    img = cv2.imdecode(bytes_as_np_array, cv2.IMREAD_UNCHANGED)

    # Convert the image to gray scale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Performing OTSU threshold
    # pipe is a bitwise OR
    ret, thresh1 = cv2.threshold(
        gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

    # Specify structure shape and kernel size.
    # Kernel size increases or decreases the area
    # of the rectangle to be detected.
    # A smaller value like (10, 10) will detect
    # each word instead of a sentence.
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))

    # Applying dilation on the threshold image
    dilation = cv2.dilate(thresh1, rect_kernel, iterations=1)

    # Finding contours
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_NONE)

    # Creating a copy of image
    im2 = img.copy()

    # A text file is created and flushed
    # file = open("recognized.txt", "w+")
    # file.write("")
    # file.close()

    # Looping through the identified contours
    # Then rectangular part is cropped and passed on
    # to pytesseract for extracting text from it
    # Extracted text is then written into the text file
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # Drawing a rectangle on copied image
        rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Cropping the text block for giving input to OCR
        cropped = im2[y:y + h, x:x + w]

        # Open the file in append mode
        # file = open("recognized.txt", "a")

        # Apply OCR on the cropped image
        text = pytesseract.image_to_string(cropped)

        text_list = text_list + text

    return serialize_parsed_text(text_list)


def parse_pdf(pdf_file):
    document = io.BytesIO(pdf_file)
    # creating a pdf reader object
    reader = PyPDF2.PdfReader(document)

    # get the text of the first page
    pdf_text = reader.pages[0].extract_text()

    return serialize_parsed_text(pdf_text)


def serialize_form_object(immutable_dict):
    # fillpdfs.print_form_fields('static/PO.pdf', sort=False, page_number=None)
    serialized_object = {}
    for field in immutable_dict:
        print(immutable_dict[field])
        serialized_object[field] = immutable_dict[field]

    # billing method checkbox
    if 'billing-method' in immutable_dict:
        serialized_object[immutable_dict['billing-method']] = "Yes"

    # carrier checkbox
    if 'carrier' in immutable_dict:
        serialized_object[immutable_dict['carrier']] = "Yes"

    # add space to account field
    if 'Dropdown3' in immutable_dict:
        split_value = immutable_dict['Dropdown3'].split("-")
        serialized_object['Dropdown3'] = " -".join(split_value)

    if not immutable_dict['ORDERED BY']:
        serialized_object['ORDERED BY'] = ""

    # set the date by the signature to be today's date
    serialized_object["Date10_af_date"] = date.today().strftime("%m/%d/%y")

    return serialized_object


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
                             path2, 2, width=500, height=500)
        
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
    print(os.listdir("static"))

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
        return parse_pdf(read_file)
