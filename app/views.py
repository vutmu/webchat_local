from flask import Flask, request, json, session
from flask import render_template

from flask_mail import Mail, Message
import random

import time

from app.dbrout import pgdb

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config.update(
    MAIL_SERVER='smtp.yandex.ru',
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_DEFAULT_SENDER='wasmoh@yandex.ru',
    MAIL_USERNAME='wasmoh11111',  # ложный юзернейм!(wasmoh)
    MAIL_PASSWORD='eluoqpoaykxcgjaz'
)
mail = Mail(app)


@app.route('/')
@app.route('/index')
def index():
    # if 'username' in session:
    #     return redirect(url_for('base'))
    return render_template('Authentification.html')


@app.route('/dbfail')
def dbfail():
    return "база данных недоступна!"


@app.route('/base')
def base():
    if 'username' in session:
        return render_template('base.html', user=session['username'])
    else:
        return "вы не авторизованы!"


@app.route("/send", methods=['GET', 'POST'])
def send():
    try:
        data = request.form
        query = (data['name'], data['text'], time.time())
        query = f"INSERT INTO messages (name, message, posting_time) VALUES {query}"
        dbresponse = pgdb(query)
        return {'status': str(dbresponse[-1][-1])}
    except Exception as err:
        return err


@app.route('/get_mess')
def get_mess():
    last_id = request.args.get('last_id')
    query = f" SELECT * FROM messages WHERE id>{last_id} LIMIT 3"
    dbresponse = pgdb(query)
    if dbresponse and dbresponse[-1][-1] == -404:
        posts = {'posts': '-404'}
        return json.dumps(posts)
    else:
        posts = [{'id': i[0], 'author': i[1], 'body': i[2]} for i in dbresponse]
        posts = {'posts': posts}
        return json.dumps(posts)


@app.route("/auth", methods=['POST', 'GET'])
def auth():
    if request.method == 'POST':
        data = request.form
        name = data.get('in_name')
        password = data['in_password']
        query = f"SELECT COUNT(*) FROM accounts where name='{name}' AND password='{password}' AND status = true;"
        dbresponse = pgdb(query)
        if dbresponse[-1][-1] == 1:
            session['username'] = name
        return json.dumps({'status': str(dbresponse[-1][-1])})
    elif request.method == 'GET':
        code = request.args.get('code')
        name = request.args.get('name')
        query = f"UPDATE accounts SET status=true WHERE name='{name}' AND checkcode={code}"
        dbresponse = pgdb(query)
        return json.dumps({'status': str(dbresponse[-1][-1])})


@app.route("/sendmail", methods=['POST'])
def sendmail():
    data = request.form
    email = data['in_email']
    name = data['in_name']
    password = data['in_password']
    checkcode = random.randint(100, 1000)
    body = f"Это письмо для регистрации! Проверочный код:{checkcode}  Если вы это" \
           f" не вы, просто проигнорируйте это письмо! :) "
    msg = Message(f"Wasmoh registration for {name}", recipients=[f"{email}"])
    msg.body = f"{body}"
    try:
        mail.send(msg)
        query = (email, name, password, checkcode)
        query = f"INSERT INTO accounts (email, name, password, checkcode) VALUES {query}"
        pgdb(query)
        return json.dumps({'status': 'sent'})
    except Exception as err:
        print(err)
        return json.dumps({'status': 'письмо не отправилось, извините!'})
