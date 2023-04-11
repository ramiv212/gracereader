import io
import pytesseract
import cv2
import numpy as np
import PyPDF2
from parse.serialize import serialize_parsed_text

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