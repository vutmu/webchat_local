import psycopg2
import os

DATABASE_URL = os.environ['DATABASE_URL']


def pgdb(query):
    try:
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(query)
        try:
            return cursor.fetchall()
        except Exception as err:
            print(err)
            return [(-200,)]  # типа код no results to fetch
    except Exception as err:
        print(err)
        return [(-404,)]  # типа код недоступной базы
