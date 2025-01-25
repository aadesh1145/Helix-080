from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# In-memory storage for simplicity, replace with a database in production
items = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q')
    # Implement your search logic here
    return f"Search results for: {query}"

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
    # Filter items based on class_name and faculty
    filtered_items = [item for item in items if item['class_name'] == class_name and item['faculty'] == faculty]
    return render_template('faculty_category.html', class_name=class_name, faculty=faculty, items=filtered_items)

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/upload_item', methods=['POST'])
def upload_item():
    title = request.form['title']
    description = request.form['description']
    price = request.form['price']
    category = request.form['category']
    faculty = request.form['faculty']
    image = request.files['image']
    filename = secure_filename(image.filename)
    
    # Ensure the upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Store item details
    items.append({
        'title': title,
        'description': description,
        'price': price,
        'class_name': category,
        'faculty': faculty,
        'image': filename
    })

    return redirect(url_for('categories'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)