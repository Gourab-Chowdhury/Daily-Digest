from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    posts = Post.query.order_by(Post.date.desc()).limit(3).all()  # Get latest 3 posts
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    posts = Post.query.all()
    return render_template('blog.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation checks
        if not all([username, email, password, confirm_password]):
            flash('All fields are required')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content, author_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('blog'))
    return render_template('write.html')

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You are not authorized to edit this post.')
        return redirect(url_for('blog'))
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Post updated successfully.')
        return redirect(url_for('blog'))
    
    return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('You are not authorized to delete this post.')
        return redirect(url_for('blog'))
    
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully.')
    return redirect(url_for('blog'))

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    author = request.args.get('author', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    sort_by = request.args.get('sort_by', 'date').strip()

    # Initialize empty search_filters list
    search_filters = []
    
    # Add filters based on provided parameters
    if query:
        search_filters.append((Post.title.ilike(f'%{query}%') | Post.content.ilike(f'%{query}%')))
    
    if author:
        # Join with User model to search by author username
        author_users = User.query.filter(User.username.ilike(f'%{author}%')).all()
        if author_users:
            author_ids = [user.id for user in author_users]
            search_filters.append(Post.author_id.in_(author_ids))
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            search_filters.append(Post.date >= start_date_obj)
        except ValueError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": "Invalid start date format. Use YYYY-MM-DD."})
            flash('Invalid start date format. Use YYYY-MM-DD.')
            return redirect(url_for('blog'))
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            search_filters.append(Post.date <= end_date_obj)
        except ValueError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"error": "Invalid end date format. Use YYYY-MM-DD."})
            flash('Invalid end date format. Use YYYY-MM-DD.')
            return redirect(url_for('blog'))
    
    # Execute the query with filters
    if search_filters:
        posts_query = Post.query
        for filter_condition in search_filters:
            posts_query = posts_query.filter(filter_condition)
            
        # Apply sorting
        if sort_by == 'date':
            posts_query = posts_query.order_by(Post.date.desc())
        elif sort_by == 'title':
            posts_query = posts_query.order_by(Post.title.asc())
        
        posts = posts_query.all()
    else:
        posts = []
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        post_data = []
        for post in posts:
            post_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author': post.author.username,
                'date': post.date.strftime('%Y-%m-%d')
            })
        return jsonify({"posts": post_data})
    
    # Handle regular page requests
    return render_template('search.html', posts=posts, query=query, author=author, 
                           start_date=start_date, end_date=end_date, sort_by=sort_by)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

if __name__ == '__main__':
    with app.app_context():
       db.create_all()
    app.run(debug=True)