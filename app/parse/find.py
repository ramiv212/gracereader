from parse.validation import is_date
import pyap
import re
from const import *


def find_addresses(full_text_array):
    # parse the image text as one big blob and
    print("*" * 10)
    fulltext = "\n".join(full_text_array)
    print(fulltext)
    print("*" * 10)
    for address in pyap.parse(fulltext, country='US'):
        print(address)
        grace_addr = address.as_dict()['full_street']
        if "24400" not in grace_addr and not "North" in grace_addr:
            return address
        

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
def find_total(text_line,response_dict_object):
    split_sub_item = text_line.split()
    for sub_item in split_sub_item:  
        if (sub_item[0].isnumeric() or sub_item[0] == "$") and sub_item[-1].isnumeric() and "." in sub_item:
            pattern = r'^(?:\$)?[\d,]+(?:\.\d{2})?$'
            regex = re.compile(pattern)
            matches = regex.findall(sub_item)
            for match in matches:
                response_dict_object.set_total(float(match.strip("$").replace(",","")))



def find_card_digits(text_line):
    if "****" in text_line or "last digits" in text_line.lower() or "XXXX" in text_line or "debit" in text_line.lower() or "xxx" in text_line:
        string_without_letter_o_or_spaces = text_line.lower().replace("o", "0").replace(" ", "")

        matches = re.findall(r"\d{3,4}", string_without_letter_o_or_spaces)
        if matches:
            return matches


def find_requested_by(card_digits):
    if card_digits in CARD_TO_NAME_DICT:
        return CARD_TO_NAME_DICT[card_digits]
    else:
        return ""


def find_amex_purchase(text_line):
    if "amex" in text_line.lower() or "american express" in text_line.lower() or "credit" in text_line.lower() or "card" in text_line.lower():
        return True


def find_vendors(text_line):
    # if vendor name is in the text line
    if any(ext in text_line.lower() for ext in VENDOR_NAMES):
        split_text_line = text_line.split(" ")
        for sub_text_item in split_text_line:
            for vendor in VENDOR_NAMES:
                if vendor in sub_text_item.lower():
                    return vendor.capitalize()