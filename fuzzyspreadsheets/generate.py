#!/usr/bin/env python

"""
Helper module for the fuzzyspreadsheets package.
generate_spreadsheet   creates a csv file with duplicate (fuzzy) rows
generate_spreadsheets  creates two csv files with duplicate (fuzzy) rows
The other functions generate random values for these two functions: name, address, company name etc
They return a tuple with the original and mangled value:  ("original", "mangled")
"""

import os
import random
import csv
from datetime import date
from .utils import construct_filepath



# Load files containing names, latin words etc. for random generation of values
DIR = os.path.join(os.path.dirname(__file__), "generate")
NAMES_FILE = os.path.join(DIR, "names.txt")
SURNAMES_FILE = os.path.join(DIR, "surnames.txt")
PEOPLE_FILE = os.path.join(DIR, "people.txt")
ADDRESS_FILE = os.path.join(DIR, "address.txt")
LATIN_FILE = os.path.join(DIR, "latin.txt")

with open(NAMES_FILE, mode='rt', encoding='utf-8') as fr:
    names = [s.strip() for s in fr.readlines() if s.strip()]

with open(SURNAMES_FILE, mode='rt', encoding='utf-8') as fr:
    surnames = [s.strip() for s in fr.readlines() if s.strip()]
    
with open(PEOPLE_FILE, mode='rt', encoding='utf-8') as fr:
    people = [s.strip() for s in fr.readlines() if s.strip()]

with open(ADDRESS_FILE, mode='rt', encoding='utf-8') as fr:
    address = [tuple(s.strip() for s in s.strip().split(',') if s.strip()) for s in fr.readlines() if s.strip()]

with open(LATIN_FILE, mode='rt', encoding='utf-8') as fr:
    latin = [s.strip() for s in fr.readlines() if s.strip()]




def generate_spreadsheet(n_rows=10, filename=None, directory=None, debugging=False):
    """Generates a spreadsheet with duplicate/similar rows.
    If debugging=True  the function saves a log file that will be used by the debugging function(s)"""
    
    global names, surnames, people, latin, address
    PROBABILITY = 0.2   #probability of identical row / of skip row
    
    # Sequence of functions generating a ceratin feature (column value)
    funcs = (generate_name, generate_surname, generate_company, generate_address, generate_tel, generate_date)
    
    # Two tables: left and right
    left, right = list(), list()
    k = 0    # id
    pre = 10**len(str(n_rows))   # row id's of duplicate rows will differ by pre   e.g. 98 == 198
    hashes = set()               # 'hashes' will keep the hashes of rows to prohibit identical examples
    log = list()
    while (len(left) + len(right)) < n_rows:
        # Generate a new example (two rows - one original and the other is mangled)
        l,r = zip(*(func() for func in funcs))
        
        # Prohibit similar examples (can happen due to radnom seed?)
        h = hash((l,r))
        if h in hashes: continue
        hashes.add(h)
        
        # Probability of being inserted
        b1,b2 = (random.random() > PROBABILITY for _ in range(2))
        if b1 or b2: 
            k += 1
            if debugging:
                log.append((len(left) if b1 else None, len(right) if b2 else None))
        if b1:
            left.append((k,)+l)
        if b2:
            right.append((pre + k,) + (r if random.random() > PROBABILITY else l))
    
    # Make a header
    header = ("id", "first name", "last name", "company", "address", "telephone", "date", "dummy")
    rows = left + right
    
    # Correct the debugging log
    if debugging:
        log = [(i, j+len(left) if j is not None else j) for i,j in log]
        log = [(j,i) if i is None else (i,j) for i,j in log]
    
    # Add a dummy column
    case = random.randint(1,5)
    dummy = [round(random.random(), 5) if case==1 else 
            random.randint(0, 999) if case==2 else
            random.randint(-9999,9999) if case==3 else
            str.join('', (chr(random.randint(97,122)) for _ in range(3,10))) if case==4 else
            "$"+str(round(random.random()*100,2))   for _ in range(len(rows))]

    # Construct file path
    filepath = construct_filepath(filename or "duplicates.csv", directory)
    
    # Write to file
    with open(filepath, mode='wt', encoding='utf-8') as fw:
        wr = csv.writer(fw)
        wr.writerow(header)
        for row,d in zip(rows,dummy):
            wr.writerow(row + (d,))

    # Write the log file to disc
    if debugging:
        filename = os.path.split(filepath)[-1].replace(".csv",'') + "_log.csv"
        path = construct_filepath(filename, directory)
        with open(path, mode='wt', encoding='utf-8') as fw:
            wr = csv.writer(fw)
            for row in log:
                wr.writerow(row)

    return filepath



def generate_spreadsheets(n_rows=10, filename1=None, filename2=None, directory=None, debugging=False):
    """Creates two csv files with fuzzily identical rows
    If debugging=True  the function saves a log file that will be used by the debugging function(s)"""
    
    global names, surnames, people, latin, address
    PROBABILITY = 0.2   #probability of identical row / of skip row
    funcs = (generate_name, generate_surname, generate_company, generate_address, generate_tel, generate_date)
    
    left, right = list(), list()
    k = 0    # id
    pre = 10**len(str(n_rows))
    hashes = set()
    log = list()   # row matching list for debugging purposes
    
    while k < n_rows:
        # Generate a new example (two rows - one original and the other is mangled)
        l,r = zip(*(func() for func in funcs))
        
        # Prohibit similar examples (can happen due to radnom seed?)
        h = hash((l,r))
        if h in hashes: continue
        hashes.add(h)
        
        # Probability of being inserted
        b1,b2 = (random.random() > PROBABILITY for _ in range(2))
        if b1 or b2: 
            k += 1
            if debugging:
                log.append((len(left) if b1 else None, len(right) if b2 else None))
        if b1: left.append((k,)+l)
        if b2: right.append((pre + k,) + (r if random.random() > PROBABILITY else l))   # i.e. identical row can be appended
        
        
    # Sort the right table (optional?)
    if not debugging: right = sorted(right, key=lambda t: t[0])   # in case the right table i assigned random id's  (for credibility)
    
    # Make a header
    header = ("id", "first name", "last name", "company", "address", "telephone", "date")
    left.insert(0, header)
    right.insert(0, header)
    
    # Add a dummy column
    case = random.randint(1,5)
    dummy = ["dummy",] + [random.random() if case==1 else 
                          random.randint(0, 999) if case==2 else
                          random.randint(-9999,9999) if case==3 else
                          str.join('', (chr(random.randint(97,122)) for _ in range(3,10))) if case==4 else
                          "$"+str(round(random.random()*100,2)) for _ in range(len(right)-1)]
    assert len(dummy)==len(right)
    
    # Construct file paths
    filepath1 = construct_filepath(filename1 or "spreadsheet1.csv", directory)
    filepath2 = construct_filepath(filename2 or "spreadsheet2.csv", directory)
    
    # Write csv files to dics
    with open(filepath1, mode='wt', encoding='utf-8') as fw:
        wr = csv.writer(fw)
        for row in left:
            wr.writerow(row)
    
    with open(filepath2, mode='wt', encoding='utf-8') as fw:
        wr = csv.writer(fw)
        for row,d in zip(right,dummy):
            wr.writerow(row + (d,))
    
    # Write the log file to disc
    if debugging:
        filename1, filename2 = (os.path.split(s)[-1].replace(".csv",'') for s in (filepath1,filepath2))
        filename = "{}_{}_log.csv".format(filename1, filename2)
        filepath = construct_filepath(filename, directory)
        with open(filepath, mode='wt', encoding='utf-8') as fw:
            wr = csv.writer(fw)
            for row in log:
                wr.writerow(row)
        
    # delete (if this function is to be used only once)
    #del names, surnames, people, latin, address
    return filepath1, filepath2



def generate_name():
    """Helper function for the generate_spreadsheet(s) wrapper-function. 
    Generates a random first name and mangles it. Returns a tuple ("origial", "mangled")"""
    
    # Use the global names list
    global names
    
    # Select a ranom name from the 'names' list
    name = names[random.randint(0, len(names)-1)]
    mangled = name[:]    # copy of name (to be mangled)
    
    # Mangling for German names
    d = str.maketrans({'ä':"ae", 'ö':"oe", 'ü':"ue", 'ß':"ss", 'Ä':"Ae", 'Ö':"Oe", 'Ü':"Ue"})
    mangled = str.translate(mangled, d)
    
    # Remove double letter (if any) (dependent on probability)
    if random.random() >= 0.5:
        l = list(mangled.lower())    # temporary
        nx = [i for i in range(len(l)-1) if len(set(l[i:i+2]))==1]   # detects the first occurence of double letters
        if nx:
            del l[nx[0]]
            mangled = str.join('', l).title()
        
    # Make other applicable transformations
    if random.random() <= 0.66:
        if mangled[-1] == 'y':
            mangled = mangled[:-1] + 'ie'
        elif mangled[-2:] in ('ie','ey'):
            mangled = mangled[:-2] + 'y'
    
    # If the name has been mangled - no more further mangling
    if name != mangled: return (name,mangled)
    
    # Other cases (one of many is a must)
    case = random.randint(1, 5)
    if case == 1:    # make a random letter double
        l = list(mangled)
        n = random.randint(1, len(l)-1)  # but not the first one (1 = starting from the second letter)
        l[n:n] = l[n].lower()
        mangled = str.join('', l)
    elif case in (2,5):   # truncate(immitates deminutive names)   (2,5) = increase the probability
        mangled = mangled[: -max(1, (len(mangled) // random.randint(2,5)))]
        if len(mangled) == 1: mangled = mangled.upper() + '.'
    elif case == 3:   # leave the intial only
        mangled = mangled[0].upper() + ('.' if random.random() > 0.3 else '')
    elif case == 4:             # fisrt name is missing
        mangled = ''
    else: pass
    
    # Return the original and manged
    return (name, mangled)
    
    

def generate_surname():
    """Helper function for the generate_spreadsheet(s) wrapper-function. 
    Generates a random last name and mangles it. Returns a tuple ("origial", "mangled")"""
    
    # Use the global surnames list
    global surnames
    
    # Select a random surname
    surname = surnames[random.randint(0, len(surnames)-1)]
    mangled = surname[:]
    
    # German names
    d = str.maketrans({'ä':"ae", 'ö':"oe", 'ü':"ue", 'ß':"ss", 'Ä':"Ae", 'Ö':"Oe", 'Ü':"Ue"})
    mangled = str.translate(surname, d)
    
    # Replace
    d = {'ea':"ie", 'sky':"ski", 'y':"i", 'ay':"ey", 'tz':"z", 'ts':"z", 'sz':"sh", 'x':"z", 'ou':"u", 'dt':"t", 'ei':"ey", 'ov':"ow", 'ski':"sky", 'ss':"s"}
    for old,new in d.items():
        if random.random() <= 0.66:
            mangled = mangled.replace(old, new)
    
    # If enogh mangling
    if surname != mangled and random.random() > 0.5:
        return (surname, mangled.title())
    
    # More mangling
    s = mangled.lower()
    l = list(s)
    nx = [i for i in range(len(s)-1) if len(set(s[i:i+2]))==1]
    if nx:
        del l[nx[0]]
        mangled = str.join('', l).title()
    elif len(l) > 3:
        del l[random.randint(1, max(1,len(mangled)-2))]
        mangled = str.join('', l)
    else:
        n = random.randint(1, len(l)-1)
        l[n:n] = l[n].lower()
        mangled = str.join('', l)
    return (surname, mangled.title())
    
    

def generate_address():
    """Helper function for the generate_spreadsheet(s) wrapper-function. 
    Generates a random address and mangles it. Returns a tuple ("origial", "mangled")"""
    
    # Use the global lists
    global people, address
    
    original = [None, None, None, None, None]
    original[0] = people[random.randint(0, len(people)-1)]
    
    ix = random.choices(range(len(address)-1), weights=range(len(address)-1, 0, -1), k=1)[0]
    original[1] = address[ix][0]
    original[2] = str(random.randint(1, 10**(random.choices(range(1,5), weights=range(5,1,-1), k=1)[0])))
    original[3] = ('' if random.random() > 0.6 else str.join('', ("WSEN"[random.randint(0,3)] for _ in range(1,random.randint(1,5))))).strip()
    if original[3]:
        original[3] += random.choice([' ', '-', '', '/'])
    original[4] = str(random.randint(10,99999))
    
    mangled = original[:]
    
    # Mangle the postal index
    case = random.randint(1,3)
    if case == 1:
        index = original[3] + original[4]
    elif case == 2:
        index = original[3][:-1] + original[4]
    elif case == 3:
        index = original[4]
    else:
        index = ''
    original[3] = ', ' + original[3] + original[4]
    mangled[3] = ', ' + index
    del original[4], mangled[4]
    if random.random() > 0.5:
        del original[-1], mangled[-1]
    
    # More mangling    
    if random.random() > 0.5:  # Remove one letter
        l = list(original[0])
        if len(l) >= 3:
            del l[random.randint(1, max(1,len(original[0])-2))]
            mangled[0] = str.join('', l)
    if random.random() > 0.5:
        mangled[1] = random.choice(address[ix])
    if random.random() > 0.5:
        s = random.choice(['','-','/', ' ', '']) + random.choice("ABCDEabcdef")
        mangled[2] += s
    if random.random() > 0.75:
        mangled = mangled[:-1]
    
    # join
    original,mangled = (str.join(' ', l).replace(" ,",',') for l in (original,mangled))
    return (original, mangled)
    



def generate_company():
    """Helper function for the generate_spreadsheet(s) wrapper-function. 
    Generates a random company name and mangles it. Returns a tuple ("origial", "mangled")"""
    
    # Use the global latin list
    global latin
    
    original = [s.title() for s in random.choices(latin, k=random.randint(1,3))]
    if random.random() > 0.5 and len(original) >=3:
        original[-1] = str.join('', [c for c in original[-1] if random.random()>0.5]).upper() or "Ltd"
    if len(original[-1]) <= 4 and random.random() > .5:
        original[-1] += '.'
    if len(original) <= 1 and random.random() > .5:
        original = [str.join('', random.choices("QWERTZUIOPASDFGHJKLYXCVBNMÜÖÄ", k=3)),] + original
    
    # Mangle
    mangled = original[:]
    case = random.randint(1,3)
    if case == 1:
        if len(mangled) > 1:
            del mangled[1 if len(mangled)==3 else -1]
        else: mangled[0] = mangled[0].upper()
    if case==2:
        if mangled[-1][-1] == '.':
            mangled[-1] = mangled[-1][:-1]
        elif len(mangled) == 1:
            mangled += [random.choice(["Ltd", "Bhd", "GmbH", "KG", "Limited", "AS", "ltd", "Co."]),]
        elif len(mangled) > 1:
            mangled = mangled[:-1]
        else:
            mangled[-1] = mangled[-1][:-1]  
    if case == 3:
        mangled = [s.upper() for s in mangled]
    
    # Change word order
    if len(mangled) >= 3 and random.random() > 0.5:
        mangled[0], mangled[1] = mangled[1], mangled[0]

    #Join
    original,mangled = (str.join(' ', l) for l  in (original,mangled))
    return (original, mangled)
    
    
    
def generate_tel():
    """Helper function for the generate_spreadsheet(s) wrapper-function. 
    Generates a random telephone number and mangles it. Returns a tuple ("origial", "mangled")"""
    
    # Make a container for tel number elements
    l = []
    l.append(str.join('', [str(random.randint(0,9)) for _ in range(random.randint(2,4))]))
    n = random.randint(2,3)
    l.extend(str(e) for e in [random.randint(10**(n-1), 10**(n)-1) for _ in range(random.randint(2,4))])
    
    def mangle(l):
        case = random.randint(1,4)
        if case == 1:
            l[0] = '(' + str(l[0]) + ') '
        elif case == 2:
            l[0] = str(l[0]) + '/'
        elif case == 3:
            l[0] = '+' + str(l[0])
        else:pass
        
        sep = '-' if random.random() > 0.5 else ' '
        s = l[0] + str.join(sep, l[1:])
            
        if random.random() < 0.2:
            s = s.replace(' ', '')
        return s
    tel1, tel2 = (mangle(l.copy()) for _ in range(2))
    return (tel1, tel2)
    
    
    
    
def generate_date():
    """Helper function for the generate_spreadsheet(s) wrapper-function. 
    Generates a random date and mangles it. Returns a tuple ("origial", "mangled")"""
    
    # Generate a random date
    dt = date.fromtimestamp(random.randint(315529200, 1609455600))
    patterns = ("%m/%d/%Y", "%m/%d/%y", "%m/%d %Y", "%Y %m/%d", "%d.%m.%Y", "%d.%m.%y",
                "%B %d, %Y", "%b %d, %Y", "%d-%m-%y", "%d-%b-%Y", "%d %b %Y", "%d%b%Y")
    p1 = random.choice(patterns)
    p2 = random.choice(patterns)
    return (dt.strftime(p1), dt.strftime(p2))


