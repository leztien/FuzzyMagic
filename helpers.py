"""
Helper functions for controller.py
including the do_backend function which is a wrapper for the detect/merge process based on the fuzzyspreadsheets library
"""


import os
from json import dump, loads
from datetime import datetime
from string import ascii_lowercase
from random import choices
from fuzzyspreadsheets import generate_spreadsheet, generate_spreadsheets, detect_duplicates, merge_spreadsheets



def do_backend(filepaths=None, operation=None, app=None):
    """
    Wrapper function for spreadsheet merging at the backend level
    filepaths: list of str or None
        a container of file-paths as strings
    returns: tuple of str
        a list or tuple of strings representing paths to the output files
    """

    # Which operation?
    operation = operation or ("merge" if (filepaths and len(filepaths) == 2) else "detect")

    # Construct folder name
    directory = "{}_{}_{}".format(operation, datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
                                   str.join('', (ascii_lowercase[ix] for ix in choices(range(26), k=5))))
    download_folder = app.config['DOWNLOAD_FOLDER'] if app is not None else "downloads"
    directory = os.path.join(download_folder, directory)

    # Make dir
    os.mkdir(directory)

    # If 'detect'
    if operation == "detect":
        if not filepaths:
            n_rows = choices(range(10, 100), weights=tuple(range(10, 100))[::-1])[0]
            filepath = generate_spreadsheet(n_rows, directory=directory, filename="spreadsheet.csv")
        else:
            filepath = filepaths[0]
        # Detect duplicates
        sorted_duplicates = detect_duplicates(filepath, filename="sorted_duplicates.csv", directory=directory)
        return [sorted_duplicates] if filepaths else [sorted_duplicates, filepath]

    # If 'merge'
    if not filepaths:   # Generate two input files
        n_rows = choices(range(10, 100), weights=tuple(range(10, 100))[::-1])[0]
        filepath1, filepath2 = generate_spreadsheets(n_rows=n_rows, directory=directory)
    else:
        filepath1, filepath2 = filepaths

    # Merge the two files
    merged_spreadsheet = merge_spreadsheets(filepath1, filepath2, directory=directory)
    return [merged_spreadsheet] if filepaths else [merged_spreadsheet, filepath1, filepath2]



def write_errorlog(dictionary, filename=None):
    """
    Custom function to write to the error log file.
    Returns True if write is ok otherwise False
    """

    # Defaults
    filename = filename or "errorlog"

    # Check dictionary type
    if not isinstance(dictionary, dict):
        from json.decoder import JSONDecodeError
        try: dictionary = loads(dictionary)
        except JSONDecodeError as err: return False

    # If file doesn't yet exist
    if not os.path.exists(filename):
        open(filename, mode='wt', encoding='utf-8').close()

    # Key 'user_agent' can get you into trouble
    if {'user_agent', 'description'}.intersection(dictionary.keys()):
        dictionary = {k: str(v) if k == 'user_agent' else v.__repr__() if k == 'description' else v for (k, v) in dictionary.items()}

    # Append the dictionary to file
    with open(filename, mode='a', encoding='utf-8', newline='\n') as f:
        dump(dictionary, f)
        f.write('\n')
    return True


def read_errorlog(filename=None):
    """
    Custom helper function to read the error log file
    """
    filename = filename or "errorlog"
    l = list()

    # Import error object
    from json.decoder import JSONDecodeError

    with open(filename, mode='rt', encoding='utf-8') as fr:
        for s in fr.read().strip().split('\n'):
            try: l.append(loads(s))
            except JSONDecodeError as err: continue
    return l


