from flask_sqlalchemy import SQLAlchemy
from flask import Flask,redirect,render_template,request,session,url_for,flash
from datetime import datetime,timedelta
from flask_mail import Mail,Message
from flask_bcrypt import Bcrypt
import psycopg2
import time


app=Flask(__name__,template_folder='template')
bcrypt=Bcrypt(app)

db_url ="postgresql://amit_pg_db_user:KGYGuoNXiIuMtnrxza67pnGDYG3GF6V3@dpg-cufpd8q3esus73e31b40-a.oregon-postgres.render.com/amit_pg_db"
app.config['SQLALCHEMY_DATABASE_URI'] =db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



#generate secret key for session
import secrets
app.secret_key=secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Keep users logged in for 7 days



#configuration for mail

# 🔹 SMTP Configuration for e1 (Sender Email)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'      # Change if using Outlook, Yahoo, Zoho (See table below)
app.config['MAIL_PORT'] = 587                     # 587 (TLS) or 465 (SSL)
app.config['MAIL_USE_TLS'] = True                 # Enable TLS
app.config['MAIL_USE_SSL'] = False                # No SSL (Use only one: TLS or SSL)
app.config['MAIL_USERNAME'] = "flaskmail369@gmail.com"     # Your sender email (e1)
app.config['MAIL_PASSWORD'] = "qpnr aqqo jijx wkss" # Your sender email's app password
app.config['MAIL_DEFAULT_SENDER'] =  "flaskmail369@gmail.com"  # Sender Email (Optional)

# 🔹 Initialize Flask-Mail
mail = Mail(app)




db=SQLAlchemy(app)

class task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name=db.Column(db.String[5000],nullable=False)
    username=db.Column(db.String[5000],nullable=True)
    email=db.Column(db.String[5000],nullable=False)
    priority=db.Column(db.String[500],nullable=False)
    date=db.Column(db.DateTime,default=datetime.utcnow)


#user login database
class users(db.Model):
    srno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username=db.Column(db.String[200],nullable=False)
    email=db.Column(db.String[200],nullable=False)
    password=db.Column(db.String[200],nullable=False)
    date=db.Column(db.DateTime,default=datetime.utcnow)


#send mail after a time
def send_mail_hours(hours,task_name,user_mail):
    time.sleep(int(hours)*3600)
    msg=f"Reminder: Your task '{task_name}' is still pending. Please complete it."
    for i in range(1,25):
        send_mail(user_mail,"Task Reminder",msg)
        time.sleep(3600)




#database connection
def get_db_connection(db_url):
    db_url =db_url # Assuming you set DATABASE_URL in Render environment variables
    # Use psycopg2 to connect to the PostgreSQL database
    conn = psycopg2.connect(db_url)
    return conn


@app.route("/",methods=['GET','POST'])
def add_todo():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_email=session['user_email']
    if request.method=='POST':
        my_task=request.form['task']
        hours=request.form['hours']
        priority_task=request.form['prio']
        todo=task(task_name=my_task,priority=priority_task,email=user_email)
        db.session.add(todo)
        db.session.commit() 

        send_mail_hours(hours,my_task,user_email)
    return render_template('todo.html',user_email=user_email)


@app.route("/delete/<string:task_name>")
def delete_task(task_name):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_mail=session['user_email']
    del_task=task.query.filter_by(task_name=task_name,email=user_mail).first()
    db.session.delete(del_task)
    db.session.commit()
    return redirect(url_for('task_manager'))


@app.route("/update/<int:task_id>",methods=['POST','GET'])
def update(task_id):
    if 'user_email' not in session['user_email']:
        return redirect(url_for('login'))
    
    task_to_update=task.query.filter_by(task_id=task_id,email=session['user_email'])

    if request.method=='POST':
        new_task=request.form['newTask']
        new_priority=request.form['newPriority']
        task_to_update.task_name=new_task
        task_to_update.priority=new_priority
        db.session.commit()
        return redirect(url_for('task_manager'))
    return render_template("update_task.html")


@app.route("/task")
def task_manager():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    else:
        user_email=session['user_email']
        altodo=task.query.filter_by(email=user_email).all()
        return render_template("task_manager.html",altodo=altodo,user_email=user_email)




@app.route("/register",methods=['GET','POST'])
def register():

    if request.method=='POST':
        user_name=request.form['username']
        user_password=request.form['password']
        user_email=request.form['email']

        conn=get_db_connection(db_url)
        cursor=conn.cursor()
        cursor.execute('SELECT email FROM users WHERE email =%s',(user_email,))
        user_data_email=cursor.fetchone()
        print(user_data_email)
        conn.close()

        if user_data_email:
            flash("Email already exists! Please log in.", "error")
            return redirect(url_for('login'))
            


        hash_password=bcrypt.generate_password_hash(user_password).decode('utf-8')
        data=users(username=user_name,email=user_email,password=hash_password)
        db.session.add(data)
        db.session.commit()
        flash("Registration successful! Please verify your email.", "success")
        return redirect(url_for('login'))
    return render_template("user_login.html")

    


@app.route("/login",methods=['POST','GET'])
def login():
    if request.method=='POST':
        user_password=request.form['password']
        user_email=request.form['email']
        session['user_email']=user_email
        conn=get_db_connection(db_url)
        cursor=conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = %s", (user_email,))
        user_data=cursor.fetchone()
        conn.close()

        if user_data:
            hash_pass = user_data[0]  # Accessing the first column (password)
            if bcrypt.check_password_hash(hash_pass,user_password):
                return redirect(url_for('add_todo'))
            else:
                flash("You Entered Wrong Password.", "error")
        else:
            return redirect(url_for('register'))

        
    return render_template("user_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/sendMail")
def send_mail(user_mail,user_subject,user_msg):

    recipient_email = user_mail
    msg = Message(
        subject=user_subject,
        recipients=[recipient_email],  # Must be a list
        body=user_msg
    )
    mail.send(msg)
    print("mail sended")
    flash("Email sent successfully!", "success")
    return redirect(url_for('add_todo'))

if __name__=='__main__':
    app.run(debug=True,port=8000)