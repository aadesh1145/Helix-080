from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    # Implement your search logic here
    return render_template('search.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/categories/<class_name>')
def class_category(class_name):
    faculties = {
        '8': ['Science', 'Math', 'English'],
        '9': ['Science', 'Math', 'English'],
        'SEE': ['Science', 'Math', 'English'],
        '11': ['Science', 'Management', 'Humanities'],
        '12': ['Science', 'Management', 'Humanities'],
        'bachelor': ['Engineering', 'Medical', 'Arts']
    }
    return render_template('class_category.html', class_name=class_name, faculties=faculties.get(class_name, []))

@app.route('/categories/<class_name>/<faculty>')
def faculty_category(class_name, faculty):
    # Implement your logic to filter items based on class_name and faculty
    return render_template('faculty_category.html', class_name=class_name, faculty=faculty)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            user = User(
                fullname=fullname,
                phone=phone,
                email=email,
                password=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            flash('Successfully registered! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Email already exists or an error occurred!', 'error')
        
    return render_template('signup.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Store user id in session
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return render_template("login.html")
            
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user id from session
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload')
@login_required
def upload():
    return render_template('upload.html')

@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)