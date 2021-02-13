"""
This module is required for deployment on gandi.net
"""

import os
os.system("pip3 install -r requirements.txt")
os.environ["PASSOWRD"] = 'pw'    # doesn't work on gandi.net
os.environ["FLASK_APP"] = 'app.py'

from app import app as application
