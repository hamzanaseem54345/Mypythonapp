from flask import Flask,request,render_template,flash,redirect,session,url_for,logging
from data import Articles
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
from functools import wraps

#from MySQLdb.cursors import DictCursor
from wtforms import Form,StringField,TextAreaField, PasswordField, validators
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


#Register Form
class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1, max=30)])
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=30)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


#Register
@app.route("/register", methods=['GET', 'POST'])
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

@app.route("/login", methods=['GET', 'POST'])
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
                session['logged_in'] = True
                session['username'] = username
                app.logger.info('Password matched')

                flash('You are succesfully Logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            #Close Connection
            cursor.close()
        else:
            error = 'Username not Found'
            return render_template('login.html',error=error)

    return render_template('login.html')

# Check if user Logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login','danger')
            return redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))





# Dashboard Route
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

#Articles
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1, max=300)])
    body = TextAreaField('Body',[validators.Length(min=50)])

# Article Route


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title=form.title.data
        body=form.body.data

        #create Cursor
        cursor = mysql.get_db().cursor()

        #Execute

        cursor.execute("insert into articles (title,body,author) values "
                       "(%s,%s,(select u.name from users u inner join articles a on u.id=a.id where u.username=%s))",
                       (title, body, session['username']))
        #cursor.execute("insert into articles(title,body,author) values(%s,%s,%s)", (title, body, session['username']))

        #commit to DB
        mysql.get_db().commit()

        #close DB
        cursor.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html',form=form)


if __name__ == "__main__":
    app.secret_key = 'Secret123'
    app.run(debug=True)