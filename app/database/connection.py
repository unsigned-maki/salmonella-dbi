import os
import time
import pymongo
import psycopg2

MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_CON_STR = os.getenv("MONGO_CON_STR")

PSQL_NAME = os.getenv("PSQL_NAME")
PSQL_USER = os.getenv("PSQL_USER")
PSQL_PASS = os.getenv("PSQL_PASS")
PSQL_HOST = os.getenv("PSQL_HOST")

class Connection:

    pass


class MongoConnection(Connection):

    def __init__(self, con_str=MONGO_CON_STR, db_name=MONGO_DB_NAME):
        self.client = pymongo.MongoClient(con_str)
        self.db = self.client[db_name]
        super().__init__()


class ContainerMongoConnection(Connection):

    def __init__(self, container):
        self.client = container.get_connection_client().test
        self.db = self.client
        super().__init__()


class SQLConnection(Connection):

    def __init__(self, host=PSQL_HOST, db_name=PSQL_NAME, user=PSQL_USER, password=PSQL_PASS):
        self.db = psycopg2.connect(dbname=db_name, user=user, password=password, host=host)
        self.db.cursor().execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id VARCHAR(255) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description VARCHAR(255),
                author VARCHAR(255) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS poll_options (
                id VARCHAR(255) PRIMARY KEY,
                poll_id VARCHAR(255) REFERENCES polls(id),
                option_text VARCHAR(255) NOT NULL,
                votes INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(20) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
        """)
        self.db.commit()
        super().__init__()


class ContainerSQLConnection(Connection):

    def __init__(self, container):
        self.db = psycopg2.connect(dbname=container.POSTGRES_DB, user=container.POSTGRES_USER, password=container.POSTGRES_PASSWORD, host=container.get_container_host_ip(), port=container.get_exposed_port(5432))
        self.db.cursor().execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id VARCHAR(255) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description VARCHAR(255),
                author VARCHAR(255) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS poll_options (
                id VARCHAR(255) PRIMARY KEY,
                poll_id VARCHAR(255) REFERENCES polls(id),
                option_text VARCHAR(255) NOT NULL,
                votes INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(20) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
        """)
        self.db.commit()
        super().__init__()
