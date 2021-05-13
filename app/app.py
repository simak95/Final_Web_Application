from typing import List, Dict
import simplejson as json
from flask import Flask, request, Response, redirect, session, url_for
from flask import render_template
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
from flask_mail import Mail, Message

app = Flask(__name__)
app.url_map.strict_slashes = False
mysql = MySQL(cursorclass=DictCursor)
mail = Mail( app )
app.secret_key = '!Qwertyuiop123!'


app.config['MYSQL_DATABASE_HOST'] = 'db'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_DB'] = 'mlbPlayers'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME']='exampleguest007@gmail.com'
app.config['MAIL_PASSWORD']='*******'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail( app )
otp = randint( 000000, 999999 )
mysql.init_app(app)


@app.route( '/login/', methods=['GET', 'POST'] )
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.get_db().cursor()
        cursor.execute( 'SELECT * FROM members WHERE username = %s AND password = %s', (username, password,) )
        account = cursor.fetchone()
        if account:
            session['signedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect( url_for( 'index' ) )
        else:
            msg = 'Incorrect username/password!'
    return render_template( 'login.html', msg=msg )


@app.route('/', methods=['GET'])
def index():
    user = {'username': 'MLB Players Project'}
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM basePlayers')
    result = cursor.fetchall()
    return render_template('index.html', title='Home', user=user, players=result)


@app.route('/stats', methods=['GET'])
def charts_view():
    legend = 'Player Count in Each Team'
    labels = []
    cursor = mysql.get_db().cursor()
    cursor.execute(
        'SELECT team FROM basePlayers GROUP BY team')
    for temp in cursor.fetchall():
        labels.append(list(temp.values())[0])
    values = []
    cursor.execute('SELECT COUNT(*) FROM basePlayers GROUP BY team')
    for temp in cursor.fetchall():
        values.append(list(temp.values())[0])
    result = cursor.fetchall()
    return render_template('chart.html', title='Home', player=result, player_labels=labels,
                           player_legend=legend,
                           player_values=values)


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