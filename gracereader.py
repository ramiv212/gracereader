# Import required packages
import cv2
import pytesseract
from dateutil.parser import parse
import numpy as np
import pyap
from fillpdf import fillpdfs
import PyPDF2

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
    
def find_date(text_line):
    # check if there is a slash in the text line
    if "/" in text_line and is_date(text_line):
        if " " in text_line:
            split_date = text_line.split()
            for sub_item in split_date:
                if "/" in sub_item:
                    return sub_item
        else:
            return sub_item
        
# basically just looks for the highest float it can find in the text blob
# not very sophisticated right now
def find_total(text_line,max_total_list):
        split_sub_item = text_line.split()
        for sub_item in split_sub_item:
            if sub_item[0].isnumeric() and sub_item[-1].isnumeric() and "." in sub_item:
                max_total_list.append(float(sub_item))
    
    
def serialize_parsed_image_text(image_text):
    full_text_array = image_text.splitlines()
    receipt_date = ""
    max_total_list = []

    if 'TOTAL' in image_text or 'DEBIT' in image_text or 'Total' in image_text:
        for text_line in full_text_array:
            if text_line != "":
                receipt_date = find_date(text_line)
                find_total(text_line,max_total_list)
        
    
        addresses = find_addresses(full_text_array)

        serialized_object = {
            "ADDRESS": addresses[0].as_dict()['full_street'],
            "CITY": addresses[0].as_dict()['city'],
            "STATE": addresses[0].as_dict()['region1'],
            "ZIP" : addresses[0].as_dict()['postal_code'],
            "Date2_af_date" : receipt_date,
            "Text1" : max(max_total_list)
        }

        print(serialized_object)
        return serialized_object
    

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
    file = open("recognized.txt", "w+")
    file.write("")
    file.close()
    
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
        
        # Appending the text into file
        # file.write(text)
        # file.write("\n")
        
        # Close the file
        # file.close

        # works here so far
    
    return serialize_parsed_image_text(text_list)

def parse_pdf(pdf_file):
    # creating a pdf reader object
    reader = PyPDF2.PdfReader(pdf_file)

    # print the number of pages in pdf file
    print(len(reader.pages))

    # print the text of the first page
    print(reader.pages[0].extract_text())

def serialize_form_object(immutable_dict):
    print(immutable_dict)
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
        
    
    print(serialized_object)
    return serialized_object
    

def create_pdf_po_document(immutable_dict):
        print(immutable_dict)
        print("\n")
        fillpdfs.write_fillable_pdf('static/PO.pdf', 'static/new.pdf', serialize_form_object(immutable_dict))


def process_as_image_or_pdf(file):
    filename = file.filename
    read_file = file.read()
    if file_extension_is_image(filename):
        return parse_image(read_file)
    else:
        return parse_pdf(read_file)