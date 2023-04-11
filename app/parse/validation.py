from dateutil.parser import parse

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


def file_extension_is_image(filename):
    file_extension = filename.split(".")[1]

    if file_extension == "png" or file_extension == "jpg" or file_extension == "jpeg" or file_extension == "webp":
        print(file_extension)
        return True, file_extension
    elif file_extension == "pdf":
        return False, file_extension
    else:
        return False,None