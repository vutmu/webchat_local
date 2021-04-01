from flask import Flask, request, json, session, url_for
from flask import render_template

from flask_mail import Mail, Message
import random
import os
import time
import redis
from dotenv import load_dotenv

from werkzeug.utils import redirect

from app.dbrout import pgdb
from app.imgbb import imgrout
from app.sessions import sessions
from app.key_generator import key_generator

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET_KEY']
app.config.update(
    MAIL_SERVER='smtp.yandex.ru',
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_DEFAULT_SENDER='wasmoh@yandex.ru',
    MAIL_USERNAME=os.environ['MAIL_USERNAME'],
    MAIL_PASSWORD=os.environ['MAIL_PASSWORD'],
    UPLOAD_FOLDER='app/static/uploads/'
)
mail = Mail(app)

# redis_host = os.environ['REDIS_HOST']
# redis_port = os.environ['REDIS_PORT']
# active_members = redis.Redis(host=redis_host, port=redis_port, db=0)
# active_keys = redis.Redis(host=redis_host, port=redis_port, db=1)
active_members = redis.from_url(os.environ.get("REDIS_URL"), db=0)
active_keys = redis.from_url(os.environ.get("REDIS_URL"), db=1)


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
                temp_key = key_generator()
                while active_keys.exists(temp_key) == 1:
                    temp_key = key_generator()
                active_members.set(name, temp_key)
                active_keys.set(temp_key, name)
                print(f'пользователь {name} авторизован. Ключ {temp_key}')

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
            data = {'title': 'Аутентификация'}
            return render_template('Authentification.html', data=data)
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
    return "база данных недоступна!"  # TODO это надо переделать


@app.route('/base', methods=['GET', 'POST'])
@sessions
def base():
    if request.method == 'GET':
        if 'subfunction' not in request.args:
            name = session['username']
            query = f"SELECT avatar from accounts WHERE name='{name}'"
            dbresponse = pgdb(query)
            avatar = dbresponse[-1][-1]
            data = {'name': name, 'avatar': avatar, 'title': 'чатик'}
            return render_template('base.html', data=data)
        elif request.args.get('subfunction') == 'get_mess':
            last_id = request.args.get('last_id')
            query = f"SELECT messages.id, messages.name, message, posting_time, avatar, user_id " \
                    f"FROM messages join accounts on " \
                    f"messages.name=accounts.name WHERE messages.id>{last_id} AND address_id=0 " \
                    f"order by messages.id LIMIT 100 "
            dbresponse = pgdb(query)
            if dbresponse and dbresponse[-1][-1] == -404:
                posts = {'posts': '-404'}
                return json.dumps(posts)
            else:
                posts = [{'id': i[0], 'author': i[1], 'body': i[2], 'posttime': i[3], 'avatar': i[4], 'user_id': i[5]}
                         for i in dbresponse]
                posts = {'posts': posts}
                return json.dumps(posts)
        elif request.args.get('subfunction') == 'logout':
            session.pop('username', None)
            return json.dumps({'status': 'logout'})
    elif request.method == 'POST':
        data = request.form
        name = session['username']
        if data['subfunction'] == 'send_mess' and data['text']:
            query = (name, data['text'], time.time())
            query = f"INSERT INTO messages (name, message, posting_time) VALUES {query}"
            dbresponse = pgdb(query)
            return {'status': str(dbresponse[-1][-1])}


@app.route('/profile/<user_id>')
@sessions
def profile(user_id):
    query = f"SELECT * FROM accounts where user_id='{user_id}'"
    dbresponse = pgdb(query)
    if len(dbresponse) > 0:
        user_id = dbresponse[-1][8]
        user = dbresponse[-1][0]
        name = session['username']
        full_avatar = dbresponse[-1][6]
        data = {'user_id': user_id, 'name': name, 'user': user, 'full_avatar': full_avatar, 'title': f'Профиль {user}'}
        return render_template("profile.html", data=data)
    else:
        return "такого челика нету!"


@app.route('/settings', methods=['GET', 'POST'])
@sessions
def settings():
    if request.method == 'GET':
        if 'subfunction' not in request.args:
            name = session['username']
            query = f"SELECT avatar, full_avatar FROM accounts where name='{name}'"
            dbresponse = pgdb(query)
            avatar = dbresponse[-1][0]
            full_avatar = dbresponse[-1][1]
            data = {'name': name, 'avatar': avatar, 'full_avatar': full_avatar, 'title': f'Настройки {name}'}
            return render_template("settings.html", data=data)
        elif request.args.get('subfunction') == 'get_pictures':  # TODO переделать в коллекцию, пофиксить
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
        data = imgrout(request.files['file'], app.config['UPLOAD_FOLDER'])
        avatar = data['avatar']
        full_avatar = data['full_avatar']
        query = f"UPDATE accounts SET avatar='{avatar}', full_avatar='{full_avatar}' WHERE name='{name}'"
        pgdb(query)
        return redirect(url_for('settings'))


@app.route('/allusers', methods=['GET', 'POST'])
@sessions
def allusers():
    if request.method == 'GET':
        if 'subfunction' not in request.args:
            name = session['username']
            query = f"SELECT * FROM accounts WHERE status=true"
            dbresponse = pgdb(query)
            users = [{'username': i[0], 'avatar': i[5], 'last_seen': i[7]} for i in
                     dbresponse]
            print(users)
            data = {'users': users, 'name': name, 'title': 'список юзеров'}
            return render_template("allusers.html", data=data)


@app.route('/games', methods=['GET', 'POST'])
@sessions
def games():
    if request.method == 'GET':
        if 'subfunction' not in request.args:
            data = {'title': 'Игры'}
            return render_template('games.html', data=data)
        elif request.args.get('subfunction') == 'get_token':
            data = {'token': active_members.get(session['username']).decode('ascii'),
                    'address': os.environ['XOXO_ADDRESS']}
            return json.dumps(data)


@app.route('/tokens', methods=['POST'])  # TODO небезопасно! Переделать!
def tokens():
    data = request.form
    if ('token' in data) and ('secret_key' in data):
        token, key = data['token'], data['secret_key']
        if key != 'very_secret_key':
            response = {'status': 'fail', 'name': 'wrong secret key between apps!'}
        elif active_keys.exists(token) == 0:
            response = {'status': 'fail', 'name': 'token not in active_keys(no such active user)'}
        else:
            name = active_keys.get(token).decode('ascii')
            response = {'status': 'success', 'name': name}
    else:
        response = {'status': 'fail', 'name': 'wrong request! missed token or secret_key!'}
    return response


@app.before_request
def bef():
    if session:
        req = str(request)
        if ('static' in req) or (request.method == 'GET' and 'subfunction' in request.args and request.args.get(
                'subfunction') == 'get_mess'):
            pass
        else:
            name = session['username']
            last_seen = time.time()
            query = f"UPDATE accounts SET last_seen='{last_seen}' WHERE name='{name}'"
            pgdb(query)
    else:
        pass
