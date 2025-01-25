from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Helper function to generate unique filename
def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return unique_filename

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

# Add Purchase Model
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')

    item = db.relationship('Item', backref='purchases')
    buyer = db.relationship('User', backref='purchases')

# Item Model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='available')
    level = db.Column(db.String(50), nullable=False)
    faculty = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    contact_no = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)

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
    # Normalize SEE/10 to consistent representation
    if class_name in ['SEE', '10']:
        class_name = '10'
    faculties = {
        '8': ['Science', 'Mathematics', 'Social Studies'],
        '9': ['Science', 'Mathematics', 'Social Studies'],
        'SEE': ['Science', 'Mathematics', 'Social Studies', 'Engineering Basics'],
        '11': ['Science', 'Management', 'Humanities', 'Education', 'Law', 'Agriculture', 'Technical and Vocational Streams'],
        '12': ['Science', 'Management', 'Humanities', 'Education', 'Law', 'Agriculture', 'Technical and Vocational Streams'],
    }
    
    if class_name in faculties:
        return render_template('faculties.html', class_name=class_name, faculties=faculties[class_name])
    else:
        items = Item.query.filter_by(level=class_name).all()
        return render_template('items.html', class_name=class_name, items=items)
@app.route('/categories/bachelor/<faculty>')
def bachelor_faculty_category(faculty):
    # Dictionary to map user-friendly faculty names to database search terms
    faculty_mapping = {
        'management-and-commerce': [
            'BBA', 'BBS', 'BBM', 'BHM', 'BTTM'
        ],
        'science-and-technology': [
            'B.Sc.', 'BIT', 'B.Sc. CSIT', 'BCA'
        ],
        'engineering': [
            'BE', 'B.Arch.'
        ],
        'medical-and-health-sciences': [
            'MBBS', 'BDS', 'B.Sc. Nursing', 'BPH', 'BAMS'
        ],
        'humanities-and-social-sciences': [
            'BA', 'B.Ed.'
        ],
        'agriculture-and-veterinary-sciences': [
            'B.Sc. Agriculture', 'BVSc & AH'
        ],
        'law': [
            'LLB'
        ],
        'fine-arts-and-media': [
            'BFA', 'BJMC'
        ]
    }

    # Check if the provided faculty is valid
    if faculty not in faculty_mapping:
        flash('Invalid faculty selected', 'error')
        return redirect(url_for('class_category', class_name='bachelor'))

    # Fetch items for the specific bachelor's faculty
    items = Item.query.filter(
        Item.level == 'bachelor',
        Item.faculty.in_(faculty_mapping[faculty])
    ).all()

    # Determine the readable faculty name for display
    readable_faculty = ' '.join(word.capitalize() for word in faculty.split('-'))

    return render_template('items.html', 
                           class_name='bachelor', 
                           faculty=readable_faculty, 
                           items=items)
@app.route('/categories/<class_name>/<faculty>')
def faculty_category(class_name, faculty):
    # Normalize class name and ensure case-insensitive faculty matching
    if class_name in ['SEE', '10']:
        class_name = '10'
    
    # Use case-insensitive faculty matching
    items = Item.query.filter(
        Item.level == class_name, 
        Item.faculty.ilike(f'%{faculty}%')
    ).all()
    
    return render_template('items.html', class_name=class_name, faculty=faculty, items=items)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['fullname'] = user.fullname
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            # Ensure the upload directory exists
            if not os.path.exists('static/uploads'):
                os.makedirs('static/uploads')
                
            title = request.form['title']
            author = request.form.get('author', '')
            description = request.form['description']
            category = request.form['category']
            status = request.form['status']
            level = request.form['level']
            contact_no = request.form['contact_no']
            email = request.form['email']
            price = request.form['price']
            file = request.files['file']
            
            # Determine faculty based on level
            if level in ['11', '12']:
                faculty = request.form.get('faculty-11-12')
            elif level == 'bachelor':
                faculty = request.form.get('faculty-bachelor')
            else:
                faculty = None
            
            # Normalize SEE/10 to consistent representation
            if level in ['SEE', '10']:
                level = '10'
            
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/uploads', filename)
                file.save(file_path)
            else:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            # Create a new item
            item = Item(
                title=title,
                author=author,
                description=description,
                category=category,
                status=status,
                level=level,
                faculty=faculty,
                price=price,
                file_path=filename,
                contact_no=contact_no,
                email=email
            )
            db.session.add(item)
            db.session.commit()
            flash('Item uploaded successfully!', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while uploading: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('upload.html')

@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return render_template('profile.html', user=user)

@app.route('/buy/<int:item_id>', methods=['POST'])
@login_required
def buy_item(item_id):
    item = Item.query.get_or_404(item_id)
    user_id = session.get('user_id')

    # Check if the user is not the item owner
    if item.email == session.get('email'):
        flash('You cannot buy your own item!', 'error')
        return redirect(url_for('items'))

    # Create purchase record
    purchase = Purchase(
        item_id=item.id,
        buyer_id=user_id,
        status='pending'
    )
    db.session.add(purchase)
    
    # Optional: Mark item as sold or reserved
    item.status = 'reserved'
    
    try:
        db.session.commit()
        flash('Purchase request sent successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing purchase: {str(e)}', 'error')

    return redirect(url_for('item_details', item_id=item_id))

@app.route('/item/<int:item_id>')
def item_details(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_details.html', item=item)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
