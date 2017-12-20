from flask import Flask,request,render_template,flash,redirect,session,url_for,logging
from data import Articles
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor

#from MySQLdb.cursors import DictCursor
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt

#from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
mysql = MySQL(cursorclass=DictCursor)
#config MYSQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'pythondb'
#app.config['MYSQL_CURSOR'] = 'DictCursor'
mysql.init_app(app)



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/articles")
def articles():
    return render_template("articles.html",articles=Articles())


@app.route("/article/<string:idnumber>/")
def article(idnumber):
    return render_template("article.html", idno=idnumber)


class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1, max=30)])
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=30)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name= form.name.data
        email= form.email.data
        username= form.username.data
        password= sha256_crypt.encrypt(str(form.password.data))


        # Create cursor

        cursor = mysql.get_db().cursor()
        #Execute Query
        cursor.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",
                       (name,email, username, password))

        #commit to DB
        mysql.get_db().commit()

        #Close connection
        cursor.close()

        flash('You are registered and can log in', 'success')

        redirect(url_for('index'))
    return render_template('register.html', form=form)

 #User Login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cursor = mysql.get_db().cursor()

        # Get user by username
        result = cursor.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            row = cursor.fetchone()
            password=row['password']


            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                app.logger.info('Password matched')
            else:
                app.logger.info('PASSWord not matched')
        else:
            app.logger.info('NO User')

    return render_template('login.html')


if __name__ == "__main__":
    app.secret_key = 'Secret123'
    app.run(debug=True)