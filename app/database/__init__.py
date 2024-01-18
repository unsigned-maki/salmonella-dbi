import os
from . import models
import pymongo
import psycopg2

"""
DB_NAME = os.getenv("PSQL_NAME")
DB_USER = os.getenv("PSQL_USER")
DB_PASS = os.getenv("PSQL_PASS")
DB_HOST = os.getenv("PSQL_HOST")

client = pymongo.MongoClient(f"mongodb://localhost:27017/")
db = client[DB_NAME]
conn = psycopg2.connect(dbname="salmonella", user="postgres", password="example", host="localhost")

class Connection:

    pass

class MongoConnection(Connection):

    def __init__(self):
        self.client = pymongo.MongoClient(f"mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:27017/")
        self.db = self.client[DB_NAME]
        super.__init__()

class SQLConnection(Connection):

    def __init__(self):
        self.db = psycopg2.connect(dbname="salmonella", user="postgres", password="example", host="localhost")
        super().__init__()
"""