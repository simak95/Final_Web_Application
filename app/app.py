
from typing import List, Dict
import simplejson as json
from flask import Flask, request, Response, redirect
from flask import render_template
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
from app import sendemail
import sys
from datetime import datetime
import random

app = Flask(__name__)
mysql = MySQL(cursorclass=DictCursor)

app.config['MYSQL_DATABASE_HOST'] = 'db'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_DB'] = 'mlbPlayers'
mysql.init_app(app)


@app.route('/', methods=['GET'])
def index():
    return render_template('login.html', title='Login Page')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html', title='Login Page')

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('register.html', title='Register Page')

@app.route('/index', methods=['GET'])
def show_index():
    user = {'username': 'Yash, Sima and Shahrukh'}
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM basePlayers')
    result = cursor.fetchall()
    return render_template('index.html', title='Home', user=user, players=result)

@app.route('/logins/new', methods=['POST'])
def add_login():
    cursor = mysql.get_db().cursor()
    strEmail = str(request.form.get('email'))

    cursor.execute('SELECT * FROM users WHERE useremail=%s', strEmail)

    row_count = cursor.rowcount
    if row_count == 0:
        strPassword = request.form.get('pswd')
        strName = request.form.get('name')
        print('No rows returned', file=sys.stderr)
        random.seed(datetime.now())
        strHash = str(random.randint(123234, 1232315324))
        inputData = (strName, strEmail, strPassword, strHash)
        sql_insert_query = """INSERT INTO users (username,useremail,userpassword,hash) 
                VALUES (%s, %s,%s, %s) """
        cursor.execute(sql_insert_query, inputData)
        mysql.get_db().commit()
        sendemail.sendemail(strEmail, strHash)
        return render_template('login.html', title='Login Page')
    else:
        print('Login already exists', file=sys.stderr)
        cursor.execute('SELECT * FROM errors where errorname=%s', 'USER_EXISTS')
        result = cursor.fetchall()
        return render_template('notify.html', title='Notify', player=result[0])

@app.route('/checklogin', methods=['POST'])
def form_check_login():
    strEmail = str(request.form.get('email'))
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM users WHERE useremail=%s', strEmail)
    row_count = cursor.rowcount
    if row_count == 0:
        print('No rows returned', file=sys.stderr)
        cursor.execute('SELECT * FROM errors where errorname=%s', 'USER_NOT_FOUND')
        result = cursor.fetchall()
        return render_template('notify.html', title='Notify', player=result[0])
    else:
        result = cursor.fetchall()

        if result[0]['hash'] != '':
            print('hash ' + result[0]['hash'], file=sys.stderr)
            cursor.execute('SELECT * FROM errors where errorname=%s', 'EMAIL_NOT_VERIFIED')
            result = cursor.fetchall()
            return render_template('notify.html', title='Notify', player=result[0])

        if str(result[0]['userpassword']) == str(request.form.get('pswd')):

            user = {'username': str(result[0]['username'])}
            cursor = mysql.get_db().cursor()
            cursor.execute('SELECT * FROM basePlayers')
            result = cursor.fetchall()
            return render_template('index.html', title='Home', user=user, players=result)

        else:
            print('Invalid Id/PWD', file=sys.stderr)
            cursor.execute('SELECT * FROM tblErrors where errName=%s', 'INVALID_LOGIN')
            result = cursor.fetchall()
            return render_template('notify.html', title='Notify', player=result[0])

@app.route('/validateLogin/<int:intHash>', methods=['GET', 'POST'])
def validateLogin(intHash):
        cursor = mysql.get_db().cursor()
        inputData = str(intHash)
        sql_update_query = """UPDATE users t SET t.Hash = '' WHERE t.Hash = %s """
        cursor.execute(sql_update_query, inputData)
        mysql.get_db().commit()
        cursor.execute('SELECT * FROM errors where errorname=%s', 'EMAIL_VERIFIED')
        result = cursor.fetchall()
        return render_template('notify.html', title='Notify', player=result[0])

@app.route('/view/<string:name>', methods=['GET'])
def record_view(name):
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM basePlayers WHERE name=%s', name)
    result = cursor.fetchall()
    return render_template('view.html', title='View Form', playn=result[0])


@app.route('/edit/<string:name>', methods=['GET'])
def form_edit_get(name):
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM basePlayers WHERE name=%s', name)
    result = cursor.fetchall()
    return render_template('edit.html', title='Edit Form', playn=result[0])


@app.route('/edit/<string:name>', methods=['POST'])
def form_update_post(name):
    cursor = mysql.get_db().cursor()
    inputData = (request.form.get('name'), request.form.get('team'), request.form.get('position'),
                 request.form.get('height'), request.form.get('weight'),
                 request.form.get('age'), name)
    sql_update_query = """UPDATE basePlayers t SET t.name = %s, t.team = %s, t.position = %s, t.height = 
    %s, t.weight = %s, t.age = %s WHERE t.name = %s """
    cursor.execute(sql_update_query, inputData)
    mysql.get_db().commit()
    return redirect("/", code=302)


@app.route('/players/new', methods=['GET'])
def form_insert_get():
    return render_template('new.html', title='New Player Form')


@app.route('/players/new', methods=['POST'])
def form_insert_post():
    cursor = mysql.get_db().cursor()
    inputData = (request.form.get('name'), request.form.get('team'), request.form.get('position'),
                 request.form.get('height'), request.form.get('weight'),
                 request.form.get('age'))
    sql_insert_query = """INSERT INTO basePlayers (name,team,position,height,weight,
    age) VALUES (%s, %s,%s, %s,%s, %s) """
    cursor.execute(sql_insert_query, inputData)
    mysql.get_db().commit()
    return redirect("/", code=302)


@app.route('/delete/<string:name>', methods=['POST'])
def form_delete_post(name):
    cursor = mysql.get_db().cursor()
    sql_delete_query = """DELETE FROM basePlayers WHERE name = %s """
    cursor.execute(sql_delete_query, name)
    mysql.get_db().commit()
    return redirect("/", code=302)


@app.route('/api/v1/players', methods=['GET'])
def api_browse() -> str:
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM basePlayers')
    result = cursor.fetchall()
    json_result = json.dumps(result)
    resp = Response(json_result, status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/players/<string:name>', methods=['GET'])
def api_retrieve(name) -> str:
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM basePlayers WHERE name=%s', name)
    result = cursor.fetchall()
    json_result = json.dumps(result)
    resp = Response(json_result, status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/players/<string:name>', methods=['PUT'])
def api_edit(name) -> str:
    cursor = mysql.get_db().cursor()
    content = request.json
    inputData = (content['name'], content['team'], content['position'],
                 content['height'], content['weight'],
                 content['age'], name)
    sql_update_query = """UPDATE basePlayers t SET t.name = %s, t.team = %s, t.position = %s, t.height = 
    %s, t.weight = %s, t.age = %s WHERE t.name = %s """
    cursor.execute(sql_update_query, inputData)
    mysql.get_db().commit()
    resp = Response(status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/players', methods=['POST'])
def api_add() -> str:
    content = request.json
    cursor = mysql.get_db().cursor()
    inputData = (content['name'], content['team'], content['position'],
                 content['height'], content['weight'],
                 content['age'])
    sql_insert_query = """INSERT INTO basePlayers (name,team,position,height,weight,
    age) VALUES (%s, %s,%s, %s,%s, %s)"""
    cursor.execute(sql_insert_query, inputData)
    mysql.get_db().commit()
    resp = Response(status=201, mimetype='application/json')
    return resp


@app.route('/api/v1/players/<string:name>', methods=['DELETE'])
def api_delete(name) -> str:
    cursor = mysql.get_db().cursor()
    sql_delete_query = """DELETE FROM basePlayers WHERE name = %s """
    cursor.execute(sql_delete_query, name)
    mysql.get_db().commit()
    resp = Response(status=200, mimetype='application/json')
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
