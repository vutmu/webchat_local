import psycopg2
from flask import Flask, request, json, session, redirect, url_for
from flask import render_template, flash

# from flask_mail import Mail, Message
# import random

import time

# import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@app.route('/')
@app.route('/index')
def index():
    return render_template('Authentification.html')


@app.route('/base')
def base():
    print('im on base')
    if 'username' in session:
        print('username in session')
        return render_template('base.html', user=session['username'])
    else:
        print('username  not in session')
        return "вы не авторизованы!"


@app.route("/send", methods=['GET', 'POST'])
def send():
    try:
        data = request.form
        query = (data['name'], data['text'], time.time())
        query = f"INSERT INTO messages (name, message, posting_time) VALUES {query}"
        pgdb(query)
        return {'Status': 'ok'}
    except:
        return 'Все норм'


@app.route('/get_mess')
def get_mess():
    last_id = request.args.get('last_id')
    query = f" SELECT * FROM messages WHERE id>{last_id} LIMIT 3"
    posts = [{'id': i[0], 'author': i[1], 'body': i[2]} for i in pgdb(query)]
    posts = {'posts': posts}
    return json.dumps(posts)


@app.route("/auth", methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':

        data = request.form
        name = data.get('in_name')
        password = data['in_password']
        query = f"SELECT COUNT(*) FROM accounts where name='{name}' AND password='{password}' AND status = true;"
        response = pgdb(query)[-1][-1]
        print('dbresponse', response)
        if response > 0:
            session['username'] = name
            return json.dumps({'status': 'ok'})
            # return redirect(url_for('base'))
        else:
            return json.dumps({'status': 'bad'})
            # return  redirect(url_for('index'))
    return "все пошло по пи..."


# TODO неправильно обрабатываются инвалидные запросы, продумать логику

def pgdb(query):
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
    except:
        pass
