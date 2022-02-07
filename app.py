"""
This module is in effect the controller of the whole web-based application.
It relies on Flask
"""


import os
from flask import Flask, render_template, request, redirect, abort, flash, send_from_directory, session
from flask_session import Session
from werkzeug.utils import secure_filename
import random
from datetime import datetime
from string import ascii_lowercase
from fuzzyspreadsheets import generate_spreadsheet, generate_spreadsheets
from helpers import do_backend, write_errorlog, read_errorlog
from operator import attrgetter


# An instance of the Flask-class is our WSGI application
app = Flask(__name__)
app.secret_key = Flask.secret_key
#from os import urandom
#app.secret_key = urandom(3)    # this is an alternative to  app.secret_key = Flask.secret_key


# Comment this block if you want sessions to be saved in flask_session instead of in a temp dir
TEMP_DIR = None
"""
from tempfile import mkdtemp
TEMP_DIR = mkdtemp()
app.config["SESSION_FILE_DIR"] = TEMP_DIR   # will use a temp folder instead of flask_session folder
"""

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
#app.config["TEMPLATES_AUTO_RELOAD"] = True  # Reload templates when they are changed. If not set, it will be enabled in debug mode
Session(app)



# Upload configurations
app.config['DOWNLOAD_FOLDER'] = "downloads"
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['MAX_CONTENT_PATH'] = 1024 * 1024 * 3  # 3 megabytes
app.config['UPLOAD_EXTENSIONS'] = ['csv',]

# Create uploads and downloads folders if not exist
for dirpath in (app.config['DOWNLOAD_FOLDER'], app.config['UPLOAD_FOLDER']):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


# Routes
@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@app.route("/generate", methods=['GET', 'POST'])
def generate():
    if request.method == 'GET':
        return render_template("generate.html")
    # If POST
    w = 'detect' if request.form.get("detect") else 'merge' if request.form.get("merge") else None
    q = request.form.get("q")  # number of rows
    n_rows = int(q)

    # Construct folder name
    directory = "generate_{}_{}".format(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
                                   str.join('', (ascii_lowercase[ix] for ix in random.choices(range(26), k=5))))
    #directory = os.path.join(app.config['DOWNLOAD_FOLDER'], directory)
    directory = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'], directory)

    # Make dir
    os.mkdir(directory)

    # If 'detect'
    if w == "detect":
        filename = "generated_spreadsheet.csv"
        filepath = generate_spreadsheet(n_rows, directory=directory, filename=filename)
    # If 'merge'
    elif w == 'merge':
        from zipfile import ZipFile
        filepath1, filepath2 = generate_spreadsheets(n_rows, filename1="generated_spreadsheet1.csv", filename2="generated_spreadsheet2.csv", directory=directory)
        filename = "generated_spreadsheets.zip"

        # A bit hackish but does the job
        cwd = os.getcwd()
        os.chdir(directory)
        #zipfilepath = os.path.join(directory, filename)
        z = ZipFile(filename, mode='w')
        try:
            z.write("generated_spreadsheet1.csv")
            z.write("generated_spreadsheet2.csv")
        except Exception as err:
            abort(500, err)
        finally:
            z.close()
        # Delete the files
        for file in (filepath1, filepath2):
            if os.path.exists(file):
                os.remove(file)
        # Change the cwd back to its original
        os.chdir(cwd)
    # If not 'detect' and not 'merge'
    else: raise ValueError("must be 'detect' or 'merge'")
    # Send
    #EITHER of these two lines should work (Flask version issues)
    return send_from_directory(directory=directory, filename=filename, as_attachment=True)
    #return send_from_directory(directory=directory, path=filename, as_attachment=True)






@app.route("/detect", methods=['GET'])
@app.route("/merge", methods=['GET'])
def detect_or_merge():
    path = str(request.path).lstrip('/')
    rs = render_template(path + ".html")    # path = request.path   # "/detect"

    # Delete the list of download_files so that the merge page loads normally the next time
    if session.get("download_files", None):
        del session["download_files"]
    return rs



@app.route('/upload', methods=['GET', 'POST'])
@app.route('/upload/<subroute>', methods=['GET', 'POST'])
def upload(subroute=None):
    # If user types url "/upload"
    if request.method != 'POST':
        return redirect("/")

    # If POST
    f1 = request.files.get('file1', None)   # f1.content_length == 0 (if no file selected)
    f2 = request.files.get('file2', None)
    files = (f1, f2) if subroute == "merge" else (f1,) if subroute == "detect" else []

    # Just in case
    if session.get("download_files"):
        del session["download_files"]

    # Case: user clicked "Generate spreadsheet(s)"
    if None in files:
        try:
            session["download_files"] = do_backend(operation=subroute)
        except Exception as err:
            abort(500, err)

    # Case: the user didn't select file(s)
    elif any(f.filename == '' for f in files):
        msg = "You must select {k1:} csv file{n:} or Generate {k2:}spreadsheet{n:}".format(
            n=('' if subroute == 'detect' else 's'),
            k1=('a' if subroute == 'detect' else "two"),
            k2=("a " if subroute == 'detect' else ''))
        flash(msg)

    # Case: the user provided two identical files
    elif len(set(f.filename for f in files)) != len(files):
        flash("You must provide two different csv files")

    # Case: not a csv file
    elif not all(os.path.splitext(f.filename)[-1][1:] in app.config['UPLOAD_EXTENSIONS'] for f in files):
        flash("{k1:} input file{k2:} must have a csv extension.".format(
            k1=("The" if subroute == 'detect' else "Both"),
            k2=('' if subroute == 'detect' else 's')))

    # Case: the user provided valid input file(s)
    else:
        filepaths = []
        prefix = "{}_{}_{}".format(subroute, datetime.now().strftime("%Y_%m_%d"),
                                          str.join('', (ascii_lowercase[ix] for ix in random.choices(range(26), k=5))))
        for (i, f) in enumerate(files):
            path = os.path.join(app.config['UPLOAD_FOLDER'], "{}_{}".format(prefix, f"{i+1}_" if subroute == "merge" else '') + secure_filename(f.filename))
            f.save(path)
            f.close()
            filepaths.append(path)
        # Try backend operation
        try: session["download_files"] = do_backend(filepaths, operation=subroute)
        except Exception as err: abort(500, err)

    # In any case
    return redirect("/" + subroute)



@app.route("/downloads/<directory>/<filename>", methods=['GET', 'POST'])
def download(directory, filename):
    # Special case to download the README.md of fuzzyspreadsheets package
    if directory == "fuzzyspreadsheets" and filename == "README.md":
        directory = os.path.join(app.root_path, directory)
    # General case
    else:
        directory = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'], directory)
    #EITHER of these two lines should work (Flask version issues)
    return send_from_directory(directory=directory, filename=filename)
    #return send_from_directory(directory=directory, path=filename)



@app.route("/about", methods=['GET', 'POST'])
def about():
    if request.method == 'GET':
        return render_template("about.html")
    # If POST, download package
    directory = "package_{}_{}".format(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
                                   str.join('', (ascii_lowercase[ix] for ix in random.choices(range(26), k=5))))
    packagename = "fuzzyspreadsheets"
    directory = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'], directory)

    # Copy the folder
    from shutil import copytree, make_archive, rmtree
    copytree(packagename, os.path.join(directory, packagename))

    # Delete __pychache__
    if os.path.exists(os.path.join(os.path.join(directory, packagename), "__pycache__")):
        rmtree(os.path.join(os.path.join(directory, packagename), "__pycache__"))

    # Archive
    archive_path = make_archive(os.path.join(directory, packagename), format='zip', root_dir=directory, base_dir=packagename)

    # Delete folder
    rmtree(os.path.join(directory, packagename))

    # Download
    #EITHER of these two lines should work (Flask version issues)
    return send_from_directory(directory=directory, filename=packagename + ".zip", as_attachment=True)
    #return send_from_directory(directory=directory, path=packagename + ".zip", as_attachment=True)




# Error handling
@app.errorhandler(404)   # file / page not found error
@app.errorhandler(400)   # bad request / bad file extension
@app.errorhandler(500)   # Internal Server Error
def error(err):
    """
    Logs error and displays an apology page
    """

    # Construct log dictionary
    request_keys = ('base_url', 'endpoint', 'path', 'referrer', 'url', 'user_agent')
    err_keys = ('code', 'description', 'name')
    d = {'date': datetime.now().strftime("%d.%m.%Y %H:%M:%S")}

    for k in request_keys:
        try: v = attrgetter(k)(request)
        except Exception: continue
        else: d[k] = v

    for k in err_keys:
        try: v = attrgetter(k)(err)
        except Exception: continue
        else: d.update({k: v})

    # Write to log
    write_errorlog(d)

    # Render apology page
    return render_template("apology.html", err=err)  # {{err | safe}}




# When debugging during development (when deploying, comment this block out)
if __name__ == "__main__":
    app.run(debug=True)

if TEMP_DIR and os.path.exists(TEMP_DIR) and TEMP_DIR not in (os.getcwd(), "/"):   # just to be on the safe side
    from shutil import rmtree
    rmtree(TEMP_DIR)







