import re


def _clean(to_clean, to_remove=[]):
    """
    Removes all \r, \n and \t characters as well as trailing and leading
    whitespace
    """

    if to_remove:
        for remove in to_remove:
            to_clean = to_clean.replace(remove, '')
    to_clean = to_clean.replace(
        '\t', '').replace('\n', '').replace('\r', '').strip()

    re.sub(' +', ' ', to_clean)

    return to_clean
