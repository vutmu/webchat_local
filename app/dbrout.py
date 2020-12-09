import psycopg2
import os


def pgdb(query):
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        sslmode = os.environ['SSL_MODE']
        connection = psycopg2.connect(DATABASE_URL, sslmode=sslmode)
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
