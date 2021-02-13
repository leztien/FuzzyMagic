# FUZZY SPREADSHEETS
#### Video Demo:  <http://www.fuzzymagic.eu/>
#### Description:
Fuzzy matching utility written in Python for spreadsheets in csv format. The main two functions of this package are:
* **detect_duplicates**: detection of (fuzzy) duplicates in a csv spreadsheet
* **merge_spreadsheets**: detection of (fuzzy) duplicates in two csv spreadsheets

The result of the first function (**detect_duplicates**) is a new csv file with the original rows rearranged so that any duplicate/similar rows go one after the other with a common new id number assigned. All unique rows follow afterwards. The user is then to decide which of the two similar rows to keep. A pair of matched rows will look like this:

| id (new)| id | first name | last name | address        | telephone          | date          |
|:-------:|----|------------|-----------|----------------|:------------------:|:-------------:|
|    1    | 42 | John       | Lüdermann | Königstraße 12 | (+40) 1234/567-890 | 31.12.98      |
|    1    |124 | Johannes   | Luederman | Konig Str. 12a | 01234 56 78 90     | Dec. 31, 1998 |


The result of the second function (**merge_spreadsheets**) is a new csv file with the data from two csv files merged into one. The user is then to decide which columns to keep and which to delete. A row in the output file looks like this:

|id (left)|id (right)|name (left)|name (right)|last name (left)|last name (right)|address (left)| address (right)|
|---------|----------|-----------|------------|----------------|-----------------|--------------|----------------|
|42       |124       | John      |Johannes    |Lüdermann       |Luederman        |Königstraße 12|Konig Str. 12a  |


The package uses fuzzy matching approaches and similarity metrics such as Levenshtein distance, token set ratio, n-grams ratio. 

For testing and demonstration purposes this package also includes spreadsheet generating functions: **generate_spreadsheet** and **generate_spreadsheets**   


## Prerequisites
Python 3
> This package doesn't use any third party libraries. Just the ones from ***Python standard library***: **os**, **sys**, **csv**, **random**, **datetime**, **functools**, **unicodedata**


## Installation
No special installation utility for this package. Just copy the folder **fuzzyspreadsheets** into your current working directory.


## Usage

Detecting duplicate (or similar) rows in a spreadsheet:

```python
from fuzzyspreadsheets import detect_duplicates

output_filepath = detect_duplicates("spreadsheet.csv")
```

Detecting duplicate (or similar) rows in two spreadsheets:
```python
from fuzzyspreadsheets import merge_spreadsheets

output_filepath = merge_spreadsheets("spreadsheet1.csv", "spreadsheet2.csv")
```


## Arguments of functions
The default parameters are:
```python
output_filepath = detect_duplicates(filepath, 
                    includes_header=True, includes_id_column=True, 
                    filename=None, directory=None, 
                    threshold=None, debugging=False)

output_filepath = merge_spreadsheets(filepath1, filepath2, 
                    includes_header=True, includes_id_column=True, 
                    filename=None, directory=None, 
                    threshold=None, columns_matching=None, debugging=False)
```

Detailed description of arguments:

filepath, filepath1, filepath2 : str
> path to the input file(s) in csv format

includes_header : bool or None
> True is expected, meaning the input table has a header row. 
If False, a generic header is added. 
If None, a basic check is conducted to determine whether the table has a header. If not, a generic header is added.

includes_id_column : bool or None
> True is expected, meaning the input table has an id column. 
If False, a generic id column is added. 
If None, a basic check is conducted to determine whether the first column is a column with unique integers. If not, a generic id column is added. 
(id columns are not used in row similarity calculations)

filename : str or None
> Desired file name for the output file. 
If None, a generic name is given.

directory : str or None
> The directory in which the output file is to be saved.
If None, the file is saved in the current working directory.

threshold : float or None
> Float between 0 and 1 denoting the (cumulative weighted) similarity ratio between two rows. 
If this ratio >= threshold then the two compared rows are considered to be duplicates of each other.
The threshold can be adjusted to improve accuracy.
If None, the default threshold is used.
The default threshold is about 0.5 (which can be changed inside the code if necessary)

columns_matching : float or None
> Float between 0 and 1 denoting the ratio between *column names matching* vs. *column values distribution comparison*.
Only used in **merge_spreadsheets** for automatic column matching between the spreadsheet serving as the left table and the one serving as the right table. The smart column matching functionality is based on *basic column names matching via similarity metrics* AND *the comparison of column values*, namely the distribution of characters in a given column. If the program fails to match columns from the two spreadsheets correctly, make sure that the input csv files have corresponding column names in both files. If the columns are arranged in the same order in both spreadsheets, you can disable this functionality by passing **columns_matching=None**. 
The **columns_matching** ratio is the ratio between these two techniques. To improve the automatic columns matching, make sure the columns in both tables have corresponding names.
To disable the automatic column matching and rely on the actual ordering of the columns, pass None.

debugging : bool
> If True, a report is printed, which includes:
> * column matching returned by the automatic column matching mechanism
> * matching pairs of row indices, as well as similarity ratios
> * matching pairs of table id's, as well as similarity ratios
> * counts of correct and incorrect matchings
> * listing of incorrectly matched rows

Note: the debugging makes sense and works ok only if the input spreadsheets are generated by the special functions in this package (see below)

Returns: output_filepath
> path pointing to the output file


## Some extra features of the package
* Smart columns matching - based on column names similarity AND comparison of the distributions of values in each column.
* Determining the column type and application of a suitable similarity function.
* Determining which of the two input spreadsheets must be used as the left and which as the right table.
* Automatic addition of a header if the input spreadsheet is missing a header. 
* Automatic addition of an id column to the input spreadsheet(s) if the first column is not recognized as a valid id column.
* Generation of real looking data spreadsheets (for testing and demonstration purposes. See details below)

## Mechanics of the algorithm
The algorithm make use of three similarity functions:
* Levenshtein ratio
* token set ratio
* n-grams ratio

> **Levenshtein ratio** is used for single word strings (e.g. first or last names)

> **token set ratio** is used for a sequence of words (e.g. company name). The functioning principle is similar to the function by the same name from the famous [fuzzywuzzy](https://pypi.org/project/fuzzywuzzy/) package.

> **n-grams ratio** is used for a mix of digits, letters and other characters (e.g. telephone number, dates)

After the individual similarity ratios for each column are calculated, they are weighted and summed, to give a cumulative similarity ratio between two rows that are being compared. Here is a visualization of this stage in the process: (the numbers used are for demonstration purpose only)
|                                | first name  | last name   | company              | telephone            |
|-------------------------------:|:-----------:|:-----------:|:--------------------:|:--------------------:|
| **row *i***                    | *John*      | *Lüdermann* | *Turbo Optimus Ltd.* | *(+40) 1234/567-890* |
| **row *j***                    | *Johannes*  | *Luederman* | *Turbo Limited*      | *01234 56 78 90*     |
| **similarity function used**   | Levenshtein | Levenshtein | token set ratio      | n-grams ratio        |
| **similarity function output** | 0.4         | 0.8         | 0.83                 | 0.75                 |
| **weights**                    | 0.25        | 0.25        | 0.3                  | 0.2                  |
| **weighted similarity**        | **0.1**     | **0.2**     | **0.25**             | **0.15**             |

| weighted similarity ratio between rows *i*,*j* |
|:----------------------------------------------:|
| **0.7**                                        |

Weighted similarity ratios between all pairs of rows are calculated in the same manner. A similarity matrix is then filled with these ratios. The row pairings are decided based on this matrix, starting with the strongest similarities. The weaker similarities are compared against the **threshold** to decide whether to deem them as matchings or not.


## Description of modules and functions in this package
### generate.py
contains functions that generate real looking data spreadsheets

> **generate_spreadsheet** generates a spreadsheet which contains unique, duplicate and similar rows. The generated spreadsheet is to be used as input into the **detect_duplicates** function.

> **generate_spreadsheets** generates two spreadsheets that contain unique, duplicate and similar rows. The generated spreadsheets are to be used as input into the **merge_spreadsheets** function.

#### Usage:
```python
from fuzzyspreadsheets import generate_spreadsheet, generate_spreadsheets
from fuzzyspreadsheets import merge_spreadsheets, detect_duplicates

# One spreadsheet for duplicates detection within
filepath = generate_spreadsheet(n_rows=100)
sorted_duplicates = detect_duplicates(filepath)

# Two spreadsheets for merging
filepath1, filepath2 = generate_spreadsheets(n_rows=50)
merged_spreadsheet = merge_spreadsheets(filepath1, filepath2)
```

> Helper functions **generate_name**, **generate_surname**, **generate_address**, **generate_company**, **generate_tel**, **generate_date**  return a tuple of two strings - one unmangled and the other - mangled element of a row. For example (*"Turbo Optimus Ltd"*, *"Turbo Limited"*)

These helper functions use respective txt files containing building blocks like names, last names, names of famous people and latin words (for construction of fake company names like *Turbo Optimus Ltd*)

For example, the **generate_address** function makes use of the **people.txt** file, which contains the names of 1000 black scientists in America, taken from [this](http://crosstalk.cell.com/blog/1000-inspiring-black-scientists-in-america) website. A generated address may look like this: "*Tyson Avenue 58*"


### model.py
contains the two core functions of this package:  **detect_duplicates** and **merge_spreadsheets** (described above)

> Helper functions in this module are: **load_rows**, **determine_column_types**, **vectorize_columns**, **match_columns**, **match_rows**, **row_similarity**, **write_rows**


### metrics.py
contains the similarity functions:

> **levenshtein_distance**, **levenshtein_ratio**, **cosine_similarity**, **token_set_ratio**, **n_grams_ratio**
> Note: the **cosine_similarity** function is used in the **token_set_ratio** to match words based on their length and first letter, before further comparison baed on Levenshtein distance.


### utils.py
contains helper utilities:
> **construct_filepath**, **strip_diacritics**

helper decorators for function's input validation:
> **check_types**, **check_empty_or_none**, **check_equivalence**

and debugging utilities:
> **debug_report**, **debug_detect_duplicates**, **debug_merge_spreadsheets**


## Integration into a web based application
This package will be used as a backend for a web page providing basic fuzzy matching functionality for spreadsheets, performed by the **detect_duplicates** and **merge_spreadsheets** functions. Flask will be used as the Controller for this web based application.


#### Notes:
This utility is my final project for Harvard's CS50 2020/2021.
Anyone is free to use and modify it.

