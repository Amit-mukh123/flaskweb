from flask_sqlalchemy import SQLAlchemy
from flask import Flask, redirect, render_template, request, session, url_for, flash, jsonify
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
import os, time
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='template')
bcrypt = Bcrypt(app)

# Load environment variables
db_url = "postgresql://amit_pg_db_user:KGYGuoNXiIuMtnrxza67pnGDYG3GF6V3@dpg-cufpd8q3esus73e31b40-a.oregon-postgres.render.com/amit_pg_db"
mail_password = os.getenv('MAIL_PASSWORD')
print(mail_password)
# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Generate secret key for session
import secrets
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = "flaskmail369@gmail.com"
app.config['MAIL_PASSWORD'] = mail_password
app.config['MAIL_DEFAULT_SENDER'] = "flaskmail369@gmail.com"

mail = Mail(app)


# Profile Picture Upload Configuration
UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Database Models
class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(5000), nullable=False)
    username = db.Column(db.String(5000), nullable=True)
    email = db.Column(db.String(5000), nullable=False)
    priority = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Users(db.Model):
    srno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(500), nullable=True, default="default.jpg")
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

#sending mails
def send_mail_task(user_mail, user_subject, user_msg):
    with app.app_context():
        msg = Message(subject=user_subject, recipients=[user_mail], body=user_msg)
        mail.send(msg)
        print("📧 Email sent successfully to:", user_mail)


@app.route("/", methods=['GET', 'POST'])
def add_todo():
    
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_email = session['user_email']
    user=Users.query.filter_by(email=user_email).first()
    if request.method == 'POST':
        my_task = request.form['task']
        hours = int(request.form['hours'])
        priority_task = request.form['prio']
        todo = Task(task_name=my_task, priority=priority_task, email=user_email)
        db.session.add(todo)
        db.session.commit()
        # send_mail_hours(hours, my_task, user_email)
    return render_template('todo.html', user_email=user_email,user=user)

@app.route("/delete/<string:task_name>")
def delete_task(task_name):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_mail = session['user_email']
    del_task = Task.query.filter_by(task_name=task_name, email=user_mail).first()
    if del_task:
        db.session.delete(del_task)
        db.session.commit()
    return redirect(url_for('task_manager'))

@app.route("/update/<int:task_id>", methods=['POST', 'GET'])
def update(task_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))
    task_to_update = Task.query.filter_by(task_id=task_id, email=session['user_email']).first()
    if not task_to_update:
        return redirect(url_for('task_manager'))
    if request.method == 'POST':
        task_to_update.task_name = request.form['newTask']
        task_to_update.priority = request.form['newPriority']
        db.session.commit()
        return redirect(url_for('task_manager'))
    return render_template("update_task.html", task=task_to_update)

@app.route("/task")
def task_manager():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_email = session['user_email']
    altodo = Task.query.filter_by(email=user_email).all()
    return render_template("task_manager.html", altodo=altodo, user_email=user_email)

@app.route("/register", methods=['GET', 'POST'])
def register():
    user = None
    if request.method == 'POST':
        user_name = request.form['username']
        user_password = request.form['password']
        user_email = request.form['email']
        profile_pic = request.files['profile_pic']

        if Users.query.filter_by(email=user_email).first():
            flash("Email already exists! Please log in.", "error")
            return redirect(url_for('login'))

        hash_password = bcrypt.generate_password_hash(user_password).decode('utf-8')

        if profile_pic and allowed_file(profile_pic.filename):
            filename = f"{user_email}_{int(time.time())}.{profile_pic.filename.rsplit('.', 1)[1].lower()}"
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = "default.jpg"  # Set default profile pic

        user = Users(username=user_name, email=user_email, password=hash_password, profile_pic=filename)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("user_login.html",user=user)



@app.route("/profile")
def profile():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    user = Users.query.filter_by(email=user_email).first()
    
    return render_template("profile.html", user=user)

@app.route("/upload_profile_pic", methods=['POST'])
def upload_profile_pic():
    if 'user_email' not in session:
        return jsonify({"success": False, "message": "User not logged in"})

    user_email = session['user_email']
    user = Users.query.filter_by(email=user_email).first()

    if 'profile_pic' not in request.files:
        return jsonify({"success": False, "message": "No file selected"})

    file = request.files['profile_pic']

    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"})

    if file and allowed_file(file.filename):
        # **Delete old profile picture before saving new one**
        if user.profile_pic and user.profile_pic != "default.jpg":
            old_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profile_pic)
            if os.path.exists(old_pic_path):
                os.remove(old_pic_path)

        # **Save new profile picture**
        filename = secure_filename(f"{user_email}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Update user profile pic in DB
        user.profile_pic = filename
        db.session.commit()

        return jsonify({"success": True, "message": "Profile picture updated!", "filename": filename})
    
    return jsonify({"success": False, "message": "Invalid file format"})



@app.route("/login", methods=['POST', 'GET'])
def login():
    user = None
    if request.method == 'POST':
        user_password = request.form['password']
        user_email = request.form['email']
        user = Users.query.filter_by(email=user_email).first()
        if user and bcrypt.check_password_hash(user.password, user_password):
            session['user_email'] = user_email  # Set session after successful login
            return redirect(url_for('add_todo'))
        flash("Invalid email or password.", "error")
    return render_template("user_login.html",user=user)

@app.route("/forgot",methods=['POST','GET'])
def forgot_password():
    if request.method=='POST':
        user_email=request.form['email']
        user_password=request.form['password']
        data=Users.query.filter_by(email=user_email).first()
        hash_password = bcrypt.generate_password_hash(user_password).decode('utf-8')
        data.password=hash_password
        db.session.commit()
        send_mail_task(user_email,"password recovery",f"your password is successfully changed.new password is: {user_password}")
        flash("Password Changed Successfully")
        return redirect(url_for('login'))

    return render_template("forgot_password.html")

@app.route("/about")
def about():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template("about.html")

@app.route("/contact")
def contact():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template("contact.html")

@app.route("/logout")
def logout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)