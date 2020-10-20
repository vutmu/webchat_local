import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']


def pgdb(query):
    connection = psycopg2.connect(DATABASE_URL, sslmode='require')
    connection.autocommit = True
    cursor = connection.cursor()
    cursor.execute(query)
    try:
        return cursor.fetchall()
    except:
        pass
