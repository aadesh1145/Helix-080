from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    items = db.relationship('Item', backref='seller', lazy=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    faculty = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))

        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('signup'))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/categories')
def categories():
    faculties = {
        '8': ['Science', 'Math', 'English'],
        '9': ['Science', 'Math', 'English'],
        'SEE': ['Science', 'Math', 'English'],
        '11': ['Science', 'Management', 'Humanities'],
        '12': ['Science', 'Management', 'Humanities'],
        'bachelor': ['Engineering', 'Medical', 'Arts']
    }
    return render_template('categories.html', faculties=faculties)

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
    # Filter items based on class_name and faculty
    filtered_items = Item.query.filter_by(class_name=class_name, faculty=faculty).all()
    return render_template('faculty_category.html', class_name=class_name, faculty=faculty, items=filtered_items)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']
        faculty = request.form['faculty']
        image = request.files['image']
        
        # Validate image
        if not image or image.filename == '':
            flash('No image selected', 'danger')
            return redirect(request.url)

        filename = secure_filename(image.filename)
        
        # Ensure the upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the image
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Create new item and associate with current user
        new_item = Item(
            title=title,
            description=description,
            price=float(price),
            class_name=category,
            faculty=faculty,
            image=filename,
            user_id=session['user_id']
        )
        
        db.session.add(new_item)
        db.session.commit()

        flash('Item uploaded successfully', 'success')
        return redirect(url_for('categories'))
    
    return render_template('upload.html')

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        flash('Please enter a search term', 'warning')
        return redirect(url_for('index'))
    
    # Search across multiple fields
    search_results = Item.query.filter(
        (Item.title.contains(query)) | 
        (Item.description.contains(query)) | 
        (Item.faculty.contains(query)) | 
        (Item.class_name.contains(query))
    ).all()
    
    return render_template('search_results.html', query=query, results=search_results)

@app.route('/about')
def about():
    return render_template('about.html')



# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)