from flask import Flask, request, json, session, url_for
from flask import render_template

from flask_mail import Mail, Message
import random
import os
import time

from werkzeug.utils import redirect

from app.dbrout import pgdb
from app.imgbb import imgrout

app = Flask(__name__)
app.secret_key = b'_5#y7L"F1Q2z\n\xec]/'
app.config.update(
    MAIL_SERVER='smtp.yandex.ru',
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_DEFAULT_SENDER='wasmoh@yandex.ru',
    MAIL_USERNAME='wasmoh',
    MAIL_PASSWORD='eluoqpoaykxcgjaz',
    UPLOAD_FOLDER='app/static/uploads/'
)
mail = Mail(app)


@app.route('/')
@app.route("/auth", methods=['POST', 'GET'])
def auth():
    if 'username' in session:  # возможно это надо переместить в гет
        return redirect(url_for('base'))
    elif request.method == 'POST':
        data = request.form
        if data['subfunction'] == 'auth':
            name = data.get('in_name')
            password = data['in_password']
            query = f"SELECT COUNT(*) FROM accounts where name='{name}' AND password='{password}' AND status = true;"
            dbresponse = pgdb(query)
            if dbresponse[-1][-1] == 1:
                session['username'] = name
            return json.dumps({'status': str(dbresponse[-1][-1])})
        elif data['subfunction'] == 'sendmail':
            name = data['in_name']
            query = f"select count(*) from accounts where name='{name}'"
            dbresponse = pgdb(query)
            if dbresponse[-1][-1] > 0:
                return json.dumps({'status': 'это имя уже занято!'})
            email = data['in_email']
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

    elif request.method == 'GET':
        if 'subfunction' not in request.args:
            return render_template('Authentification.html')
        elif request.args['subfunction'] == 'validation':
            checkcode = request.args.get('code')
            name = request.args.get('name')
            query = f"SELECT COUNT(*) FROM accounts WHERE name='{name}' AND checkcode='{checkcode}' "
            dbresponse = pgdb(query)
            if dbresponse[-1][-1] != 1:
                return json.dumps({'status': 'валидация не прошла!'})
            else:
                query = f"UPDATE accounts SET status=true WHERE name='{name}' AND checkcode={checkcode}"
                pgdb(query)
                session['username'] = name
                return json.dumps({'status': 'валидация успешна!'})


@app.route('/dbfail')
def dbfail():
    return "база данных недоступна!"


@app.route('/base', methods=['GET', 'POST'])
def base():
    if 'username' in session:
        if request.method == 'GET':
            if 'subfunction' not in request.args:
                name = session['username']
                query = f"SELECT avatar from accounts WHERE name='{name}'"
                dbresponse = pgdb(query)
                avatar = dbresponse[-1][-1]
                data = {'name': name, 'avatar': avatar}
                return render_template('base.html', data=data)
            elif request.args.get('subfunction') == 'get_mess':
                last_id = request.args.get('last_id')
                query = f"SELECT messages.id, messages.name, message, posting_time, avatar " \
                        f"FROM messages join accounts on " \
                        f"messages.name=accounts.name WHERE messages.id>{last_id} LIMIT 100 "
                dbresponse = pgdb(query)
                if dbresponse and dbresponse[-1][-1] == -404:
                    posts = {'posts': '-404'}
                    return json.dumps(posts)
                else:
                    posts = [{'id': i[0], 'author': i[1], 'body': i[2], 'posttime': i[3], 'avatar': i[4]} for i in
                             dbresponse]
                    posts = {'posts': posts}
                    return json.dumps(posts)
            elif request.args.get('subfunction') == 'logout':
                session.pop('username', None)
                return json.dumps({'status': 'logout'})
        elif request.method == 'POST':
            data = request.form
            if data['subfunction'] == 'send_mess':
                query = (data['name'], data['text'], time.time())  # Возможно надо поменять data['name'] на session[
                # 'username']
                query = f"INSERT INTO messages (name, message, posting_time) VALUES {query}"
                dbresponse = pgdb(query)
                return {'status': str(dbresponse[-1][-1])}
    else:
        return redirect(url_for('auth'))


@app.route('/profile/<user>')
def profile(user):
    if "username" in session:
        query = f"SELECT * FROM accounts where name='{user}'"
        dbresponse = pgdb(query)
        if len(dbresponse) > 0:
            name = dbresponse[-1][0]
            avatar = dbresponse[-1][5]
            data = {'name': name, 'avatar': avatar}
            return render_template("profile.html", data=data)
        else:
            return "такого челика нету!"
    else:
        return redirect(url_for('auth'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if "username" in session:
        if request.method == 'GET':
            if 'subfunction' not in request.args:
                name = session['username']
                query = f"SELECT * FROM accounts where name='{name}'"
                dbresponse = pgdb(query)
                name = dbresponse[-1][0]
                avatar = dbresponse[-1][5]
                data = {'name': name, 'avatar': avatar}
                return render_template("settings.html", data=data)
            elif request.args.get('subfunction') == 'get_pictures':
                path = 'app/static/images'
                pictures = [i for i in os.walk(path)]
                data = {'pictures': pictures[-1][-1]}
                return json.dumps(data)
            elif request.args.get('subfunction') == 'change_avatar':
                name = session['username']
                avatar = request.args.get('avatar')
                query = f"UPDATE accounts SET avatar='{avatar}' WHERE name='{name}'"
                pgdb(query)
                return json.dumps({'status': '??'})
        elif request.method == 'POST':
            name = session['username']
            ref = imgrout(request.files['file'], app.config['UPLOAD_FOLDER'])
            query = f"UPDATE accounts SET avatar='{ref}' WHERE name='{name}'"
            pgdb(query)
            return redirect(url_for('settings'))
    else:
        return redirect(url_for('auth'))
