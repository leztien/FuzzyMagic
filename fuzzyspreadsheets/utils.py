#!/usr/bin/env python

"""
utility functions for the fuzzyspreadsheets package
"""


import os, csv
from functools import wraps


# Decorator with arguments
def check_types(*types, **types_dict):    # types_dict  will be ignored here
    """Pass the types as arguments into this decorator e.g.  check_types(int, str, int)"""
    def decorator(func):
        @wraps(func)
        def closure(*args, **kwargs):
            """Checks for types matching"""
            if len(types) != len(args):
                raise IndexError("Inconsisten number of types vs args")
            if not all(type(typ) is type for typ in types):
                raise TypeError("The arguments passed to the decorator must be type's")
            for i,(arg,typ) in enumerate(zip(args, types)):
                if type(arg) is not typ:
                    raise TypeError("Argument at position {} must be of type '{}' and not '{}'"\
                                    .format(i+1, typ.__name__, type(arg).__name__))
            return func(*args, **kwargs)
        return closure
    return decorator



def check_empty_or_none(func):
    """Make the function return 0 instead of None (to avoid arithmetic errors further in code)"""
    @wraps(func)
    def closure(*args, **kwargs):
        if not (args[0] and args[1]):
            return 0.0
        return func(*args, **kwargs)
    return closure



def check_equivalence(func):
    @wraps(func)
    def closure(*args, **kwargs):
        if args[0] == args[1]:
            return 1.0
        return func(*args, **kwargs)
    return closure



#Usage Example:
@check_types(str, str)   # this will be checkd first
@check_empty_or_none     # this will be checked second
@check_equivalence       # this will be checked last
def f1(s1, s2):
    """doc of f1"""
    if not (s1 and s2):
        return None
    return ...   # arbitrary operation
#s = f1("Abc", "Abc")




def construct_filepath(filename=None, directory=None):
    """Constructs filepath from provided directory+filename. Flexible functionality"""
    # defaults
    filename = filename or "spreadsheet.csv"
    if not str(filename).endswith(".csv"): filename = str(filename) + ".csv"
    directory = str(directory or os.getcwd())
    
    # If directory doesnt exist, maybe - expanduser?
    temp = None
    if not os.path.exists(directory):
        temp = os.path.expanduser("~/" + directory.strip('/')+'/')
    
        # If still not exists then create the dir
        if not os.path.exists(temp):
            temp = None
            os.makedirs(directory.strip('/'))

    # Assign and check
    directory = temp or directory
    assert os.path.exists(directory)    
    
    # Join dir-path with file-path
    return os.path.join(directory, filename)




import unicodedata
def strip_diacritics(s):
    """Removes diacretics and umlauts from a string"""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')




def debug_report(func):
    """Prints detaled information.
    This function gives wrong results if the input spreadsheet(s) had no valid id column"""
    
    if not hasattr(func, "debugging_matchings"): return
    debugging_matchings = func.debugging_matchings
    lt = [(i and int(str(i)[-min(len(str(i)), len(str(j))):]), j and int(str(j)[-min(len(str(i)), len(str(j))):])) for (i,j,*_) in debugging_matchings]
    true_matchings = sum((i==j) if None not in (i,j) else 0 for (i,j) in lt)
    false_matchings = sum((i!=j) if None not in (i,j) else 0 for (i,j) in lt)
    unmatchings = len([i if i is not None else j for (i,j) in lt if None in (i,j)]) - len({i if i is not None else j for (i,j) in lt if None in (i,j)})
    
    # Print report
    print("\n\nREPORT ({})".format("detect_duplicates" if func.__name__ == "detect_duplicates" else "merge_spreadsheets"))
    print("==============================")
    if hasattr(func, "column_matchings"):
        print("\ncolumn matchings:")
        print(func.column_matchings)
        if hasattr(func, "column_types"): print("column types:", func.column_types)
    print("\nrankings: (the pairs are list indeces, not actual id's from the table(s))")
    print(" pair  similarity ratio  " + ("offset-ratio" if len(func.rankings[0])==4 else ''))
    #print(func.rankings)
    for row in func.rankings: 
        print(("({:>3} {:>3}) {:>6.2f}" + ("{:>17.2f}" if len(row)==4 else '')).format(*row))
    print("\ndebugging_matchings:\nnote: in the following report the actual id's from the spreadsheet(s) are used.\nIt gives correct results only if the input files were generated by generate_spreadsheet(s) function")
    print(*debugging_matchings, sep='\n', end='\n')
    print("total:          ", len(debugging_matchings))
    print("true matchings: ", true_matchings)
    print("false matchings:", false_matchings)
    print("unmachings:     ", unmatchings)
    


def debug_detect_duplicates(filepath, rows, row_matchings):
    """
    Debugging report for the detect_duplicates function.
    Work only with the generated files.
    """
    directory = os.path.split(filepath)[0]
    filename = os.path.split(filepath)[-1].replace(".csv",'') + "_log.csv"
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        print(f"\nLog file '{filepath}' for debugging not found")
        return
    
    # Open the log file
    with open(filepath, mode='rt', encoding='utf_8') as fr:
        log = tuple(csv.reader(fr))
    
    # Process
    log = [tuple(None if v in ('', None) else int(v) for v in t) for t in log]

    # Loop
    n_correct_matchings = 0
    row_matchings = list(row_matchings)   # use a copy
    for t in log:
        if tuple(t) in row_matchings:
            row_matchings.remove(tuple(t))
            n_correct_matchings += 1
    
    # Print report
    print(f"\n\nREPORT (detect_duplicates)\nbased on log file '{filepath}':")
    print("==================================================")
    print("total:            ", len(log))
    print("correct matchings:", n_correct_matchings)
    print("wrong matchings:  ", sum(1 for t in row_matchings if (None not in t)))
    print("failed matchings: ", sum(1 for t in row_matchings if (None in t)))
    
    # Analize bad matchings
    if row_matchings: print("\nbad matchings in detail:")
    for t in row_matchings:
        print(t)
        if t[0]: print(rows[t[0]])
        if t[1]: print(rows[t[1]])
        print()
    print("--- end of report ---\n".upper())




def debug_merge_spreadsheets(file_left, file_right, rows_left, rows_right, row_matchings):
    """
    Debugging report for the merge_spreadsheets function.
    Work only with the generated files.
    """
    
    directory = os.path.split(file_left)[0]
    filename1, filename2 = (os.path.split(s)[-1].replace(".csv",'') for s in (file_left, file_right))
    filename = "{}_{}_log.csv".format(filename1, filename2)
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        filename1, filename2 = (os.path.split(s)[-1].replace(".csv",'') for s in (file_right, file_left))
        filename = "{}_{}_log.csv".format(filename1, filename2)
        path = os.path.join(directory, filename)
    if not os.path.exists(path):
        print("\nLog file for debugging not found")
        return
    
    # Open the log file
    with open(path, mode='rt', encoding='utf_8') as fr:
        rd = csv.reader(fr)
        log = tuple(rd)
    
    # Process
    log = [tuple(None if v in ('', None) else int(v) for v in t) for t in log]
    
    # If file were switched
    a,b = ([max(v for v in a if v) for a in zip(*lt)] for lt in (log, row_matchings))
    if a != b: 
        row_matchings = [(b,a) for a,b in row_matchings]   # swap
        rows_left, rows_right = rows_right, rows_left
    

    
    # Loop
    n_correct_matchings = 0    # counter
    row_matchings = list(row_matchings)   # use a copy
    for t in log:
        if tuple(t) in row_matchings:
            row_matchings.remove(tuple(t))
            n_correct_matchings += 1
    
    # Print report
    print("\n\nREPORT (merge_spreadsheets)\nbased on log file '{}':".format(os.path.split(path)[-1]))
    print("===========================================")
    print("total:            ", len(log))
    print("correct matchings:", n_correct_matchings)
    print("wrong matchings:  ", sum(1 for t in row_matchings if (None not in t)))
    print("failed matchings: ", sum(1 for t in row_matchings if (None in t)))
    
    # Analize bad matchings
    if row_matchings: print("\nbad matchings in detail:")
    for t in row_matchings:
        print(t)
        if t[0]: print(rows_left[t[0]])
        if t[1]: print(rows_right[t[1]])
        print()
    print("--- end of report ---\n".upper())
        
    