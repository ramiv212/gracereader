import io
import cv2
import pytesseract
from dateutil.parser import parse
import numpy as np
import pyap
from fillpdf import fillpdfs
import PyPDF2
from datetime import date

VENDOR_NAMES = ['amazon','walmart']

def file_extension_is_image(filename):
    file_extension = filename.split(".")[1]
    if file_extension == "png" or file_extension == "jpg" or file_extension == "jpeg" or file_extension == "webp":
        return True
    elif file_extension == "pdf":
         return False

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
    months_array = ["January","February","March","April","May","June","July","August","September","October","November","December"]
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
def find_total(text_line,max_total_list):
        split_sub_item = text_line.split()
        for sub_item in split_sub_item:
            if (sub_item[0].isnumeric() or sub_item[0] == "$") and sub_item[-1].isnumeric() and "." in sub_item:
                max_total_list.append(float(sub_item.strip("$")))


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
    
def serialize_parsed_text(image_text):
    print(image_text)
    full_text_array = image_text.splitlines()
    addresses = find_addresses(full_text_array)
    receipt_date = ""
    max_total_list = []
    is_amex_purchase = False
    vendor_name = ""

    if 'TOTAL' in image_text or 'DEBIT' in image_text or 'Total' in image_text:
        for text_line in full_text_array:
            if text_line != "":
                find_total(text_line,max_total_list)

                if find_amex_purchase(text_line):
                    is_amex_purchase = True

                # fix this later. It returns none because this is being searched for overe every line of text
                if not find_date(text_line) == None:
                    receipt_date = find_date(text_line)
                
                if find_vendors(text_line):
                    vendor_name = find_vendors(text_line)
        

        if not addresses:
            return {
            "VENDOR NAME": vendor_name,
            "Date2_af_date" : receipt_date,
            "Text1" : max(max_total_list),
            "Check Box10": is_amex_purchase
        }
        else:
            return {
            "VENDOR NAME": vendor_name,
            "ADDRESS": addresses[0].as_dict()['full_street'],
            "CITY": addresses[0].as_dict()['city'],
            "STATE": addresses[0].as_dict()['region1'],
            "ZIP" : addresses[0].as_dict()['postal_code'],
            "Date1_af_date" : date.today().strftime("%m/%d/%y"),
            "Date2_af_date" : receipt_date,
            "Text1" : max(max_total_list),
            "Check Box10": is_amex_purchase
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
    ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    
    # Specify structure shape and kernel size.
    # Kernel size increases or decreases the area
    # of the rectangle to be detected.
    # A smaller value like (10, 10) will detect
    # each word instead of a sentence.
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    
    # Applying dilation on the threshold image
    dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)
    
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
    fillpdfs.print_form_fields('static/PO2.pdf', sort=False, page_number=None)
    serialized_object = {}
    for field in immutable_dict:
        serialized_object[field] = immutable_dict[field]

    # billing method checkbox
    if immutable_dict['billing-method']:
        serialized_object[immutable_dict['billing-method']] = "Yes"

    # carrier checkbox
    if immutable_dict['carrier']:
        serialized_object[immutable_dict['carrier']] = "Yes"

    # add space to account field
    if immutable_dict['Dropdown3']:
        split_value = immutable_dict['Dropdown3'].split("-")
        serialized_object['Dropdown3'] = " -".join(split_value)
        
    
    return serialized_object
    

def create_pdf_po_document(immutable_dict):
        fillpdfs.write_fillable_pdf('static/PO.pdf', 'static/new.pdf', serialize_form_object(immutable_dict))


def process_as_image_or_pdf(file):
    filename = file.filename
    read_file = file.read()
    if file_extension_is_image(filename):
        return parse_image(read_file)
    else:
        print(parse_pdf(read_file))
        return parse_pdf(read_file)