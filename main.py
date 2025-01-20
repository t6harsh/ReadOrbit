from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.secret_key = 'harsh_secrete'


basedir=os.path.abspath(os.path.dirname(__file__))
path_to_db = os.path.join(basedir , "Database/library_management_system.db")

app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///" + path_to_db

db = SQLAlchemy(app)

app.app_context().push()

def get_db():
    return db
from controllers import *

if __name__ =="__main__":
    app.run(debug=True)
