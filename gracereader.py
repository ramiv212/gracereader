# Import required packages
import cv2
import pytesseract
from dateutil.parser import parse
import numpy as np
import pyap
import PyPDF2

# reader = PyPDF2.PdfReader('sample7.pdf')

# print(reader.pages[0].extract_text())

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


def file_extension_is_image(file_name):
    file_extension = ".".split(file_name)[1]
    if file_name == "png" or file_name == "jpg" or file_name == "webp":
        return True
    elif file_name == "pdf":
         return False
    
def serialize_parsed_image_text(image_text):
    text = image_text

    maxTotalList = []

    if 'TOTAL' in text or 'DEBIT' in text or 'Total' in text:
        textList = text.splitlines()

        for item in textList:
            if item != "":
                # find date
                if "/" in item and is_date(item):
                    print(item)

                # find total (highest float number)
                split_sub_item = item.split()
                for sub_item in split_sub_item:
                    if sub_item[0].isnumeric() and sub_item[-1].isnumeric() and "." in sub_item:
                        maxTotalList.append(float(sub_item))

        print(max(maxTotalList))

        fulltext = " ".join(textList)

        addreses = pyap.parse(fulltext, country='US')

        print(addreses[0].as_dict())
    

def parse_image(image_file):
    if file_extension_is_image:
        # Read image from which text needs to be extracted
        bytes_as_np_array = np.frombuffer(image_file.read(), dtype=np.uint8)
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

        # each text string will be appended to this list to be serialized later
        text_list = ""
        
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
    
    serialize_parsed_image_text(text_list)