from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send
import MySQLdb
from apscheduler.schedulers.background import BackgroundScheduler
import webbrowser
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = '^my_secret^'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/web'
app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from website import routes

