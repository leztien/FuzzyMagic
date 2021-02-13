#!/usr/bin/env python

"""
The core module of the fuzzyspreadsheets package, where the main job is done.
detect_duplicates and mainly merge_spreadsheets  are wrapper functions.
The rest of these functions are helper functions for these two.
"""


import csv
import os
import sys
import unicodedata
from .metrics import cosine_similarity, levenshtein_ratio, token_set_ratio, n_grams_ratio
from .utils import construct_filepath
from .utils import debug_report, debug_detect_duplicates, debug_merge_spreadsheets




def detect_duplicates(filepath: 'path to the input spreadsheet', 
                      includes_header: 'the first row is the header' = True,
                      includes_id_column: 'the first column is an id column with unique integers' = True,
                      filename: 'output file name' = None, 
                      directory: 'output directory' = None, 
                      threshold: 'similarity probability threshold' = None, 
                      debugging=False) -> 'output file path':
    """Detects duplicates in a csv file and sorts rows: duplicates first, unique rows at the bottom
    This function expects the input spreadsheet to have a header and id column, unless inicated explicetely"""
    
    # Defaults
    threshold = threshold or 0.45
    
    # Get column types
    column_types = determine_column_types(filepath, includes_header=includes_header, includes_id_column=includes_id_column)
    
    # Load rows
    header, rows = load_rows(filepath, includes_header=includes_header, includes_id_column=includes_id_column)
    includes_id_column = True   # because load_rows()  automatiucally adds an id column if missing
    
    # Make a square matrix    
    m = n = len(rows)
    mx = [];  [mx.append([0,]*n) for _ in range(m)]   # square matirx
    
    # Compute matching ratios
    for (i, _) in enumerate(rows):
        #See the progress
        if debugging and len(rows) >= 40:
            sys.stdout.write('\r' + ("Progress:" + str(round(i/n*100)).rjust(3) + "%")) # \r prints a carriage return first, so s is printed on top of the previous line
            sys.stdout.flush()  # comment out if not necessary
            
        for j in range(i+1, len(rows)):
            mx[i][j] = row_similarity(rows[i], rows[j],
                         column_types=column_types,
                         includes_id_column=includes_id_column)
    # Print a new line after the progress bar
    if debugging and len(rows) >= 40: 
        sys.stdout.write('\r' + ("Progress:100%"))
        print()
    
    # Reflect the mx
    [mx[i].__setitem__(j, mx[j][i]) for i in range(len(rows)) for j in range(len(rows)) if j<i]
    
    # Sort
    rankings = list()
    for i,row in enumerate(mx):
        rankings.append((i, row.index(max(row)), max(row)))
    rankings = sorted(rankings, reverse=True, key=lambda t: t[2]) 
    
    # For debugging purposes
    debugging_matchings = list()
    
    # Make matchings
    matchings = list()
    nx = set(t[0] for t in rankings)  # remove is the method
    
    for (i,j,r) in rankings:
        match = r >= threshold   # arbitrary threshold values
        if match and (j in nx) and (i in nx):
            matchings.append((i,j))
            nx.remove(i)
            nx.remove(j)   # prevent double matching
            if debugging:
                debugging_matchings.append((int(rows[i][0]), int(rows[j][0]), round(r,2)))
    
    # Sort the matchings lt
    matchings = sorted(matchings, key=lambda t: t[0])
    
    # Add unmatched rows
    [matchings.append((i,None)) for i in nx]
    
    # Debugging
    if debugging:
        debugging_matchings = sorted(debugging_matchings, key=lambda t: t[0])
        [debugging_matchings.append((int(rows[i][0]), None, '?')) for i in sorted(nx)]
        
        #Stuff for the debugging report
        from inspect import stack
        this = globals().get(stack()[0].function)
        if this:
            this.mx = mx
            this.rankings = rankings
            this.matchings = matchings
            this.debugging_matchings = debugging_matchings 
        debug_report(this)
        debug_detect_duplicates(filepath, rows, matchings)
    
    # Unravel the indeces
    nx_unravelled = [i for i in sum(matchings, ()) if i is not None]
    assert len(nx_unravelled) == len(set(nx_unravelled))
    
    # Make new index
    g = zip(sum(((i,i) for i in range(len(matchings))), ()), sum(matchings, ()))
    nx_new = [i for i,j in g if j is not None]
    assert len(nx_new) == len(nx_unravelled)
    
    # Make new header
    header = ("id(new)",) + tuple(header)
    
    # Construct output filepath
    output_filepath = construct_filepath(filename=filename or "sorted_duplicates.csv", directory=directory)
    
    # Write to file
    output_filepath = output_filepath or "output.csv"
    with open(output_filepath, mode='wt', encoding='utf_8') as fw:
        wr = csv.writer(fw)
        wr.writerow(header)
        for (i,ix) in zip(nx_unravelled, nx_new):
            row = (ix + 1,) + tuple(rows[i])
            wr.writerow(row)
    return output_filepath



def merge_spreadsheets(filepath1: 'path to the first spreadsheet', filepath2: 'path to the second spreadsheet',
                       includes_header: 'the first row is the header' = True,
                       includes_id_column: 'the first column is an id column with unique integers' = True,
                       filename: 'output file name' = None, directory: 'output directory' = None, 
                       threshold: 'similarity probability threshold' = None, 
                       columns_matching: 'ratio of column names matching vs. vectorized values distribution technique' = None,
                       debugging=False) -> 'output file path':
    """Merges two spreadsheets into one detecting and combining any duplicates.
    This function expects that both spreadsheets have an id column with unique integers,
    unless explicetely indicated in the arguments (includes_id_column).
    (this function is a wrapper function, executing the spreadsheet merging process)"""
    
    file_left, file_right, column_matchings, column_types = match_columns(filepath1, filepath2,
                                                includes_header=includes_header,
                                                includes_id_column=includes_id_column,
                                                ignore_column_types_when_matching_columns=False,
                                                proportion_of_column_names_similarity=columns_matching)
    header_left,  rows_left  = load_rows(file_left,  includes_header=includes_header, includes_id_column=includes_id_column)
    header_right, rows_right = load_rows(file_right, includes_header=includes_header, includes_id_column=includes_id_column)
    
    row_matchings = match_rows(rows_left, rows_right, column_matchings, column_types, 
                               threshold=threshold, debugging=debugging)
    
    # Construct output filepath
    output_filepath = construct_filepath(filename=filename or "merged_spreadsheet.csv", directory=directory)
    
    output_filepath = write_rows(header_left, rows_left, header_right, rows_right,
                                   column_matchings, row_matchings,
                                   output_filepath=output_filepath)
    # Debug
    if debugging:
        debug_merge_spreadsheets(file_left, file_right, rows_left, rows_right, row_matchings)   # the new (short) report (comes second)
    return output_filepath




def vectorize_columns(filepath, includes_header=None, includes_id_column=None):
    """
    This function returns:
        Vectors for each column (except the first column - i.e. id column)
        Each of these vectors is in effect a discrete distribution of "the bag of characters" in a given column.
        This function also returns the spreadsheets header and
        the number of rows in that spreadsheet.
        (not a very elegant implementation for the sake of expense - in order to avoid another opening of a file for reading)
    """
    
    header, rows = load_rows(filepath, includes_header=includes_header, includes_id_column=includes_id_column)
    includes_id_column = True  # load_rows() adds a generic id column if not found a valid one
    ix = int(includes_id_column)  # will be used as the starting index:  1=start from the nsecond column
    
    n_columns = len(header) - int(includes_id_column)   # 0 = the second column  (skipping the id column)
    ll = list();  [ll.append([]) for _ in range(n_columns)]
    lll = list(); [lll.append([]) for _ in range(n_columns)]   # lengths
    
    for row in rows:
        [ll[i].extend(ord(c) for c in str(v).upper()) for (i,v) in enumerate(row[ix:])]
        [lll[i].append(len(str(v))) for (i,v) in enumerate(row[ix:])]
    
    # Average length of values
    m = len(lll[0])   # m = number of rows in the table
    lengths = [sum(l)/m for l in lll]
    
    # Construct a vector
    vectors = [[l.count(n) for n in range(32,91)]+[length,] for l,length in zip(ll,lengths)]
    return (vectors, header, m)  # n vectors each with 59 components (where n = number of columns in the csv file)




def determine_column_types(filepath, includes_header=None, includes_id_column=None):
    """
    Determines column types:  0 = word   1 = set    2 = digits+alpha
    These types (integers) will be used to match the appropriate function from similarity calculation
    Returns: a tuple of integers
    """
    
    # Load data
    header, rows = load_rows(filepath, includes_header=includes_header, includes_id_column=includes_id_column)
    
    # Table has id column?
    includes_id_column = True    # because load_rows() checks whether the first column is a valid id column and adds a generated id column if necessary
    slicer = slice(1,None,None) if includes_id_column else slice(None,None,None)
    
    # Determin the number of columns
    n_columns = len(header) - int(includes_id_column)
    ll = list();  [ll.append([]) for _ in range(n_columns)]
    
    for row in rows:
        for (v,l) in zip(row[slicer], ll):
            v = str(v).strip().lower()
            if sum(c.isdigit() for c in v) > sum(c.isalpha() for c in v):
                l.append(2)  # case = digits+
            else:
                l.append(0 if max(len(v.split(' ')), len(v.split(','))) <= 1 else 1)
    
    # Find modes
    ll = [[(v, l.count(v)) for v in set(l)] for l in ll]
    column_types = [sorted(l, key=lambda t: t[-1], reverse=True)[0][0] for l in ll]
    return tuple(column_types)




def match_columns(filepath1, filepath2,
                  includes_header=None, includes_id_column=True,
                  proportion_of_column_names_similarity=None,
                  ignore_column_types_when_matching_columns=False):
    """
    Determines which file will serve as the left and right tables.
    Matches columns from these two files - based on char distribution AND column names similarities.
    This function expects spreadhseets with id columns, unless explicetely indicated as includes_id_column=False
    Returns:
        file_left, file_right : file_names determined to serve as the left and right tables respectively
        column_matchings : list of tuples. Each tuple represents columns matching. 
            for example (0,1) menas the first column from the 'left' table (zero-based but not counting the id column)
            matches the second column from the 'right' table.
            for example (6, None) means the sevent column (zero-based but not counting the id column)
            will match none of the columns from the 'right' table
        column_types : a list of integers denoting a type of each colummn from the 'left' table (?)
    """
    
    # Defaults
    proportion_of_column_names_similarity = proportion_of_column_names_similarity or 0.5
    
    vectors_1, header_1, m1 = vectorize_columns(filepath1, includes_header=includes_header, includes_id_column=includes_id_column)
    vectors_2, header_2, m2 = vectorize_columns(filepath2, includes_header=includes_header, includes_id_column=includes_id_column)
    
    types_1 = determine_column_types(filepath1, includes_header=includes_header, includes_id_column=includes_id_column)
    types_2 = determine_column_types(filepath2, includes_header=includes_header, includes_id_column=includes_id_column)
    
    # Here 'left' means the table with the smaller number of columns
    condition = len(header_1) <= len(header_2)
    vectors_left, vectors_right = (vectors_1, vectors_2) if condition else (vectors_2, vectors_1)
    header_left, header_right = (header_1, header_2)  if condition else (header_2, header_1)
    types_left, types_right = (types_1, types_2) if condition else (types_2, types_1)
    m_left, m_right = (m1, m2) if condition else (m2,m1)
    file_left, file_right = (filepath1, filepath2) if condition else (filepath2, filepath1)
    
    cosine_similarities = [[cosine_similarity(a, b) for b in vectors_right] for a in vectors_left]
    
    # At this point the headers automatically include an id column
    ix = 1   # i.e. start from index 1 skipping the id column
    
    # Get similarity ratios of the header names
    n_grams_ratios = [[n_grams_ratio(a, b, n=2) for b in header_right[ix:]] for a in header_left[ix:]]
    assert len(n_grams_ratios) == len(header_left) - 1, "error"   # seems to work
    #assert len(n_grams_ratios) == len(header_1) - 1, "error"  #original
    
    p = proportion_of_column_names_similarity   # proportion of header-name similaritiy    (0.2 - 0.6  ok)
    cosine_and_n_grams = [[sum([v1*(1-p), v2*(p)])/2 for (v1,v2) in zip(l1,l2)] for (l1,l2) in zip(cosine_similarities, n_grams_ratios)]
    
    column_matchings = []
    column_types = []

    left_indeces = zip(list(range(len(header_left)-1)), (max(l) for l in cosine_and_n_grams))
    left_indeces,_ = zip(*sorted(left_indeces, key=lambda t: t[-1], reverse=True))
    right_indeces = list(range(len(header_right)-1))
        
    for ix_left in left_indeces:
        l = cosine_and_n_grams[ix_left].copy()
        ix_right = l.index(max(l))
        
        if not ignore_column_types_when_matching_columns:
            while types_left[ix_left] != types_right[ix_right] and sum(l)>0:
                l[ix_right] = 0
                ix_right = l.index(max(l))
        
        ix_right = None if (sum(l)==0 or ix_right not in right_indeces) else ix_right
        column_matchings.append((ix_left, ix_right))
        if ix_right in right_indeces: right_indeces.remove(ix_right)
        if ix_right is not None:
            column_types.append((ix_left, types_left[ix_left]))
    
    #column_matchings = combined_corr = [(i, a.index(max(a))) for (i,a) in enumerate(cosine_and_n_grams)]
    column_matchings = sorted(column_matchings, key=lambda t: t[0])
    column_types = [t[1] for t in sorted(column_types, key=lambda t: t[0])]
    unmatched_columns = [(None,ix) for ix in range(len(header_right)-1) if ix not in [t[1] for t in column_matchings]]
    column_matchings += unmatched_columns
    
    # Here 'left' will mean the table with the fewer rows
    condition = m_left <= m_right
    file_left, file_right = (file_left, file_right) if condition else (file_right, file_left)
    if not condition: column_matchings = [(t[1], t[0]) for t in column_matchings]
    return (file_left, file_right, column_matchings, column_types)




def row_similarity(row_left, row_right, column_matchings=None, column_types=None, includes_id_column=True):
    """
    Given two rows calculates their similarity
    By default this function expects both rows with id column, unless explicetely indicated in the arguments

    Parameters
    ----------
    row_left : tuple or list representing one row of a table
    row_right : tuple or list representing one row of a table (against which the first row will be compared)
    column_matchings : a list of tuples, optional
        the tuples are pairs of column indeces indicatingmatchings from the left table to the right.
        The default is None.
    column_types : a list of int, optional
        The integer corresponds to a similarity function which will be used on the values in a given column.
        The default is None.
    includes_id_column : bool, optional
        Expects True. Automatically the rows will have an id column at this time anyway. 
        The default is True.

    Returns
    -------
    float
        ratio denoting the similarity.
    """
   
    # Make defaults if not provided
    includes_id_column = True if includes_id_column is True else False
    n = min(len(row_left), len(row_right)) - int(includes_id_column)
    column_matchings = column_matchings or [(i,i) for i in range(n)]
    column_types = column_types or [1 for _ in range(n)]   # 1 = token_set_ratio  (as default function)
    
    # Rows include id?
    if includes_id_column:
        row_left, row_right = (row[1:] for row in (row_left, row_right))
    
    # Preprocess both rows (by removing diacretics and umlauts, and converting to upper case)
    row_left, row_right = ([''.join(c for c in unicodedata.normalize('NFD', str(v)) if unicodedata.category(c) != 'Mn').upper() for v in row] for row in (row_left, row_right))
    
    # Drop None's in matchings
    column_matchings = [t for t in column_matchings if None not in t]
    
    # Similarity Functions 
    funcs = (levenshtein_ratio, token_set_ratio, n_grams_ratio)
    weights = {0:2,   1:1,   2:1} 
    weights = [weights[k] for k in column_types]
    weights = [w/sum(weights) for w in weights]
    funcs = [funcs[i] for i in column_types]
    
    # Check
    assert len(funcs) == len(column_matchings), "assert len(funcs) == len(column_matchings)"
    assert min(len(row_left), len(row_right)) >= len(funcs)
    
    # Iterate over column values
    ratios = []
    for (ix_left, ix_right), func in zip(column_matchings, funcs):
        v1 = row_left[ix_left]
        v2 = row_right[ix_right]
        ratios.append(func(v1,v2))
    
    # If None in ratios - exclude None's (dor not recalibrate weights because this would slant the chances towards the remaining value(s))
    ratios = (r or 0 for r in ratios)    # turns None's into zeros
    
    # Weighted sum of the ratios
    return sum(r*w for r,w in zip(ratios,weights))
    
    


def load_rows(filepath, includes_id_column=None, includes_header=None):
    """
    Loads rows from file

    Parameters
    ----------
    filepath : str
        path to the csv file
    includes_id_column : bool, optional
        If False - adds a generic id column. 
        If True or None - checks for a valid id column and adds if necessary
        The default is None.
    includes_header : bool, optional
        If False - adds a generic header.
        If True or None - checks and adds if necessary
        The default is None.

    Returns
    -------
    header : tuple/list of str
    rows : a list of tuples
        each tuple represents a row in a table.
    """
    
    # Get the file path right
    if not os.path.exists(filepath):
        filepath = os.path.expanduser(filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"file not found: {filepath}")
        
    # make sure the file is a csv file
    if os.path.splitext(filepath)[-1] != ".csv":
        raise TypeError("filepath must point to a csv file")
    
    # Open and read the file
    with open(filepath, mode='rt', encoding='utf-8') as fr:
        rows = tuple(csv.reader(fr))
    
    # Determine about the header
    if includes_header is None:
        if any(c.isnumeric() for c in ''.join([str(col) for col in rows[0]])):
            includes_header = False
    if includes_header:
        header, rows = rows[0], rows[1:]
    else:
        header = tuple(f"Column {i+1}" for i in range(len(rows[0])))
    
    # Check that the first column is a valid INTEGER id colum
    first_column = [row[0] for row in rows]
    ids = (int(v) for v in first_column if isinstance(v, int) or str(v).isdigit())
    bad_id_column = len(set(ids)) != len(first_column)
    
    # If the first column is not a valid id column
    if bad_id_column or (includes_id_column is False):
        rows = [(i,) + tuple(row) for (i, row) in enumerate(rows)]
        header = ("_id_",) + tuple(header)
    return (header, rows)




def match_rows(rows_left, rows_right, column_matchings, column_types, includes_id_column=True, 
               threshold: 'similarity probability threshold' = None, debugging=False):
    """
    Finds matching rows. 
    This function expects both rows to start with an id column, unless explicetely inicated so as includes_id_column=False

    Parameters
    ----------
    rows_left : a list of tuples. Each tuple is a pair of int's
        Each tuple represents a row from the table serving as the left table.
    rows_right : a list of tuples. Each tuple is a pair of int's
        Each tuple represents a row from the table serving as the right table.
    column_matchings : a list of tuples. Each tuple is a pair of int's
        Each tuple represents a column matching.
        E.g. (0,1) means the zero'th column fomr the left column matches the 1'st column from the second
    column_types : a sequence of int's
        Each integer denotes a type and corresponds to the appropriate similarity function.
    includes_id_column : bool, optional
        Expects True. The default is True.
    threshold : similarity probability threshold, optional
        Can be adjusted to improve the accuracy. The default is None.
    debugging : bool, optional
        Works only with the generated csv files. Prints a report on matching. The default is False.

    Returns
    -------
    matchings : a list of tuples
        Each tuple denotes row matchings.
        E.g. (0, 12) means the zero'th row from the first table matches the 12#th row from the second
    """
    
    # Defaults
    threshold = threshold or 0.49
    
    # Create matrix
    m,n = (len(rows_left), len(rows_right))
    mx = [];  [mx.append([0,]*n) for _ in range(m)]
    
    # Compute matching ratios
    for i,row_left in enumerate(rows_left):
        #See the progress
        if debugging and max(m,n) >= 40:
            sys.stdout.write('\r' + ("Progress:" + str(round(i/n*100)).rjust(3) + "%")) # \r prints a carriage return first, so s is printed on top of the previous line
            sys.stdout.flush()  # comment out if not necessary
            
        for j,row_right in enumerate(rows_right):
            mx[i][j] = row_similarity(row_left=row_left, row_right=row_right,
                         column_matchings=column_matchings,
                         column_types=column_types,
                         includes_id_column=includes_id_column)
    # Print a new line after the progress bar
    if debugging and max(m,n) >= 40: 
        sys.stdout.write('\r' + ("Progress:100%"))
        print()
    
    # Sort
    rankings = list()
    ln = len(mx[0])
    for i,row in enumerate(mx):
        mm = max(row)   # maximum value
        offset_ratio = 1 - ((sum(row) - mm)/(ln-1) / mm)
        rankings.append((i, row.index(mm), mm, offset_ratio))
    rankings = sorted(rankings, reverse=True, key=lambda t: t[2])
    
    # For debugging purposes
    debugging_matchings = list()
    
    # Make matchings
    matchings = list()
    right_indeces = set(t[1] for t in rankings)  # remove is the method
    
    for i,j,r,o in rankings:
        match = (o >= 0.49 and r >= 0.25) or r >= threshold   # arbitrary threshold values
        if match and (j in right_indeces):
            matchings.append((i,j))
            right_indeces.remove(j)   # prevent double matching
            if debugging:
                debugging_matchings.append((int(rows_left[i][0]), int(rows_right[j][0]), round(r,2)))
    
    # Sort the matchings lt
    matchings = sorted(matchings, key=lambda t: t[0])
    
    # Add unmatched rows
    left_indeces = set(range(m)).difference({t[0] for t in matchings})
    right_indeces = set(range(n)).difference({t[1] for t in matchings})
    [matchings.append((i,None)) for i in left_indeces]
    [matchings.append((None,j)) for j in right_indeces]
    
    # Debugging
    if debugging:
        debugging_matchings = sorted(debugging_matchings, key=lambda t: t[0])
        [debugging_matchings.append((int(rows_left[i][0]), None,  round(rankings[[row[0] for row in rankings].index(i)][2],2))) for i in sorted(left_indeces)]
        [debugging_matchings.append((None, int(rows_right[j][0]), '?')) for j in sorted(right_indeces)]

        # Stuff for the debugging report
        from inspect import stack
        this = globals().get(stack()[0].function)
        if this:
            this.column_matchings = column_matchings
            this.column_types = column_types
            this.mx = mx
            this.rankings = rankings
            this.matchings = matchings
            this.debugging_matchings = debugging_matchings 
        debug_report(this)   # the old (long) report (comes first)

    # Return matchings
    return matchings




def write_rows(header_left, rows_left, header_right, rows_right,
               column_matchings, row_matchings,
               output_filepath=None):
    """
    Merges a row from the left and a row from the right tables into a single row.
    The header is merged into one long header as well.
    This function is only used by the merge_spreadsheets function

    Parameters
    ----------
    header_left : tuple of str
        Header of the left table.
    rows_left : a lits of tuples
        Each tuple represents a row from the left table
    header_right : tuple of str
        header of the right table.
    rows_right : a list of tuples
        Each tuple represents a row from the right table
    column_matchings : a list of tuples
        see the docs of the functions above.
    row_matchings : a sequence of int's
        see the docs of the functions above.
    output_filepath : str, optional
        A default name for the file is passed ("merged_spreadsheets.csv"). The default is None.

    Returns
    -------
    output_filepath : str
        output file path
    """

    # Sort the column mathings for prettyness
    column_matchings = sorted(column_matchings, key=lambda t: (10000 if t[0] is None else ((t[0] + 1)*100) + (1000 if t[1] is None else (t[1]+1)*1 )) )
    
    # Make big header
    header = [header_left[0] + " (left)", header_right[0] + " (right)"]
    keys_left = [header[0],]
    keys_right = [header[1],]
    indeces_left = [0,]
    indeces_right = [0,]
    
    for t in column_matchings:
        if t[0] is not None:
            k = header_left[t[0]+1] + " (left)"
            header.append(k)
            keys_left.append(k)
            indeces_left.append(t[0]+1)
        if t[1] is not None:
            k = header_right[t[1]+1] + " (right)"
            header.append(k)
            keys_right.append(k)
            indeces_right.append(t[1]+1)
    
    # Compile and write
    output_filepath = output_filepath or "output.csv"
    with open(output_filepath, mode='wt', encoding='utf_8') as fw:
        wr = csv.writer(fw)
        wr.writerow(header)
        for l,r in row_matchings:
            d = {k:None for k in header}
            if l is not None:
                row_left = rows_left[l]
                d.update({k:v for k,v in zip(keys_left, (row_left[j] for j in indeces_left))})
            if r is not None:
                row_right = rows_right[r]
                d.update({k:v for k,v in zip(keys_right, (row_right[j] for j in indeces_right))})
            row = [d[k] for k in header]
            wr.writerow(row)
    return output_filepath



