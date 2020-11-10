import psycopg2
import os


def pgdb(query):
    try:
        if 'DATABASE_URL' in os.environ:
            DATABASE_URL = os.environ['DATABASE_URL']
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            connection = psycopg2.connect(
                database='simple_messenger',
                user='force',
                password='12345',
                host='localhost',
                port='5432',
            )
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
