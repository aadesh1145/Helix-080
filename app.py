from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user
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

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# models.py or within app.py if models are defined there

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    purchases = db.relationship('Purchase', backref='buyer', lazy=True)

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
    purchases = db.relationship('Purchase', backref='item', lazy=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(100))
    delivery_address = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    cancellation_reason = db.Column(db.Text)

@app.route('/search')
def search():
    query = request.args.get('q')
    if query:
        items = Item.query.filter(
            Item.title.ilike(f'%{query}%') |
            Item.author.ilike(f'%{query}%') |
            Item.description.ilike(f'%{query}%')
        ).all()
    else:
        items = []
    return render_template('search_results.html', items=items, query=query)

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
    faculty_mapping = {
        'management-and-commerce': ['BBA', 'BBS', 'BBM', 'BHM', 'BTTM'],
        'science-and-technology': ['B.Sc.', 'BIT', 'B.Sc. CSIT', 'BCA'],
        'engineering': ['BE', 'B.Arch.'],
        'medical-and-health-sciences': ['MBBS', 'BDS', 'B.Sc. Nursing', 'BPH', 'BAMS'],
        'humanities-and-social-sciences': ['BA', 'B.Ed.'],
        'agriculture-and-veterinary-sciences': ['B.Sc. Agriculture', 'BVSc & AH'],
        'law': ['LLB'],
        'fine-arts-and-media': ['BFA', 'BJMC']
    }

    if faculty not in faculty_mapping:
        flash('Invalid faculty selected', 'error')
        return redirect(url_for('class_category', class_name='bachelor'))

    items = Item.query.filter(
        Item.level == 'bachelor',
        Item.faculty.in_(faculty_mapping[faculty])
    ).all()

    readable_faculty = ' '.join(word.capitalize() for word in faculty.split('-'))

    return render_template('items.html', class_name='bachelor', faculty=readable_faculty, items=items)

@app.route('/categories/<class_name>/<faculty>')
def faculty_category(class_name, faculty):
    if class_name in ['SEE', '10']:
        class_name = '10'
    
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
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
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
    items = Item.query.all()
    return render_template('index.html', items=items)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
                
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
            
            if level in ['11', '12']:
                faculty = request.form.get('faculty-11-12')
            elif level == 'bachelor':
                faculty = request.form.get('faculty-bachelor')
            else:
                faculty = None
            
            if level in ['SEE', '10']:
                level = '10'
            
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
            else:
                flash('No file selected', 'error')
                return redirect(request.url)
            
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
    user = current_user
    orders = Purchase.query.filter_by(buyer_id=user.id).all()
    items = Item.query.filter_by(email=user.email).all()  # Assuming email is used to identify user's uploads
    return render_template('profile.html', user=user, orders=orders, items=items)

@app.route('/buy/<int:item_id>', methods=['GET', 'POST'])
@login_required
def buying_page(item_id):
    item = Item.query.get_or_404(item_id)
    
    if request.method == 'POST':
        purchase = Purchase(
            item_id=item_id,
            buyer_id=current_user.id,
            payment_method=request.form['payment_method'],
            transaction_id=request.form.get('transaction_id', ''),
            delivery_address=request.form['delivery_address'],
            phone_number=request.form['phone_number'],
            email=request.form['email']
        )
        
        db.session.add(purchase)
        db.session.commit()
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_completion', order_id=purchase.id))
        
    return render_template('buying_page.html', item=item)

@app.route('/order_completion/<int:order_id>')
@login_required
def order_completion(order_id):
    order = Purchase.query.get_or_404(order_id)
    return render_template('order_completion.html', order=order)

@app.route('/item/<int:item_id>')
def item_details(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_details.html', item=item)

@app.route('/all_items')
def all_items():
    sort_by = request.args.get('sort_by', 'title')
    category = request.args.get('category')
    status = request.args.get('status')

    query = Item.query

    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)

    if sort_by == 'title':
        query = query.order_by(Item.title)
    elif sort_by == 'price':
        query = query.order_by(Item.price)
    elif sort_by == 'author':
        query = query.order_by(Item.author)

    items = query.all()
    return render_template('all_items.html', items=items, sort_by=sort_by, category=category, status=status)

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.email != current_user.email:
        flash('You do not have permission to edit this item.', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        item.title = request.form['title']
        item.author = request.form.get('author', '')
        item.description = request.form['description']
        item.category = request.form['category']
        item.status = request.form['status']
        item.level = request.form['level']
        item.contact_no = request.form['contact_no']
        item.email = request.form['email']
        item.price = request.form['price']
        
        db.session.commit()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_item.html', item=item)

@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.email != current_user.email:
        flash('You do not have permission to delete this item.', 'error')
        return redirect(url_for('profile'))

    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/cancel_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def cancel_order(order_id):
    order = Purchase.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash('You do not have permission to cancel this order.', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        reason = request.form['reason']
        order.status = 'cancelled'
        order.cancellation_reason = reason
        db.session.commit()
        flash('Order cancelled successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('cancel_order.html', order=order)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)