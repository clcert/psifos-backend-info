from flask import Flask
import configparser
from sqlalchemy import create_engine

app = Flask(__name__)

# Configuring Environment Variables
config = configparser.ConfigParser()
config.read('.env')

# Connection credentials
db_user = config['local']['user']
db_pass = config['local']['password']
db_host = config['local']['host']
db_name = config['local']['database']

# configuring our database uri
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://{0}:{1}@{2}/{3}".format(db_user, db_pass, db_host, db_name)

engine = create_engine("mysql://{0}:{1}@{2}/{3}".format(db_user, db_pass, db_host, db_name))

from app import ballots_views, elections_views, trustees_views, voters_views
