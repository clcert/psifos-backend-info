import os

from flask import Flask
from sqlalchemy import create_engine

app = Flask(__name__)

# Connection credentials
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_name = os.getenv("DB_NAME")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

db_url = "mysql://{0}:{1}@{2}/{3}".format(db_user, db_pass, db_host, db_name)

# configuring our database uri
app.config["SQLALCHEMY_DATABASE_URI"] = db_url

engine = create_engine(db_url)
