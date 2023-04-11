from parse.find import find_addresses,find_date,find_total,find_card_digits,find_requested_by,find_amex_purchase,find_vendors
from datetime import date
from const import PO_NUMBER_BY_PERSON
from response_dict import Response

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
    response_dict_object = Response()
  
    full_text_array = image_text.splitlines()
    addresses = find_addresses(full_text_array)


    for text_line in full_text_array:
        if text_line != "":

            find_total(text_line,response_dict_object)

            if find_amex_purchase(text_line):
                response_dict_object.set(**{"Check Box10": True})

            # fix this later. It returns none because this is being searched for overe every line of text
            if not find_date(text_line) == None:
                response_dict_object.set(**{"Date2_af_date": find_date(text_line)})

            if find_vendors(text_line):
                response_dict_object.set(**{"VENDOR NAME": find_vendors(text_line)})

            if find_card_digits(text_line):
                card_digits = find_card_digits(text_line)[0]
                response_dict_object.set(card_digits = card_digits)

                if card_digits:
                    requested_by = find_requested_by(card_digits)
                    response_dict_object.set(**{"ORDERED BY": requested_by})
                    response_dict_object.set(NUMBER = generate_po_number(requested_by))
        
            receipt_total = response_dict_object.get_total()
            response_dict_object.set(Text1 = receipt_total)

        if addresses:
            response_dict_object.set(
                ADDRESS       = addresses.as_dict()['full_street'],
                CITY          = addresses.as_dict()['city'],
                STATE         = addresses.as_dict()['region1'],
                ZIP           = addresses.as_dict()['postal_code'],
            )
    
    response_dict_object.set(Date1_af_date = date.today().strftime("%m/%d/%y"))
    
    response_dict_object.print()
    return response_dict_object.get()


def serialize_form_object(immutable_dict):
    # fillpdfs.print_form_fields('static/PO.pdf', sort=False, page_number=None)
    serialized_object = {}
    for field in immutable_dict:
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