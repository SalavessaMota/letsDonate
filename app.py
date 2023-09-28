import os
from flask import Flask, request, redirect, url_for, render_template, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import sqlite3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = sqlite3.connect("doacoes.db")
# Create the 'users' table
db.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                username TEXT UNIQUE NOT NULL,
                hash TEXT NOT NULL,
                contact TEXT NOT NULL)''')

# Create the 'items' table
db.execute('''CREATE TABLE IF NOT EXISTS items
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, 
                image_file TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id))''')


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
def index():
    db = sqlite3.connect("doacoes.db")
    items = db.execute("SELECT * FROM items")

    username = None
    if 'user_id' in session:
        cursor = db.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
        user_row = cursor.fetchone()
        if user_row:
            username = user_row[0]

    return render_template("index.html", items=items, username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return "not possible"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "not possible"

        # Query database for username
        db = sqlite3.connect("doacoes.db")
        cursor = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        row = cursor.fetchone()

        # Ensure username exists and password is correct
        if row is None or not check_password_hash(row[2], request.form.get("password")):
            return "not possible"

        # Remember which user has logged in
        session["user_id"] = row[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    

def login_required(f):    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        username = request.form['username']
        contact = request.form['contact']
        with sqlite3.connect('doacoes.db') as db:
            cur = db.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            existing_user = cur.fetchone()
            
            if existing_user:
                # The username already exists, handle it (perhaps show an error message)
                return "Este nome de utilizador ou contacto telefónico já existe, por favor altere os dados."            
            
            password = request.form['password']
            hashed_password = generate_password_hash(password, method='scrypt')
            
            cur.execute("INSERT INTO users (username, hash, contact) VALUES (?, ?, ?)", (username, hashed_password, contact))
            db.commit()

        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        user_id = session["user_id"]
        file = request.files['file']
        item_name = request.form.get("item_name")
        item_description = request.form.get("item_description", "")
        item_location = request.form.get("item_location", "")
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            with sqlite3.connect('doacoes.db') as db:
                db.execute("INSERT INTO items (name, image_file, description, location, user_id) VALUES (?, ?, ?, ?, ?)",
                           (item_name, filename, item_description, item_location, user_id))
        return redirect("/")    
    return render_template('add_item.html')

@app.route('/delete_item', methods=['POST'])
@login_required
def delete_item():
    item_id = request.form.get("item_id")
    with sqlite3.connect("doacoes.db") as db:
        cur = db.cursor()
        cur.execute("SELECT image_file FROM items WHERE id = ?", (item_id,))
        image_file = cur.fetchone()
        if image_file:
            os.remove(image_file[0])  # Delete the image file from filesystem
        cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
        db.commit()
    return redirect("/")


@app.route('/contact_info/<int:user_id>', methods=['GET'])
@login_required
def contact_info(user_id):
    """Show contact information for a specific user."""
    
    # Connect to the database
    db = sqlite3.connect("doacoes.db")
    cursor = db.execute("SELECT username, contact FROM users WHERE id = ?", (user_id,))
    user_info = cursor.fetchone()
    
    username, contact = user_info
    
    return render_template("contact_info.html", username=username, contact=contact)


@app.route("/item_table")
def view_items():
    db = sqlite3.connect("doacoes.db")
    items = db.execute("SELECT * FROM items")

    username = None
    if 'user_id' in session:
        cursor = db.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
        user_row = cursor.fetchone()
        if user_row:
            username = user_row[0]
    return render_template("item_table.html", items=items)


@app.route("/aboutus")
def aboutus():
    return render_template("about_us.html")


if __name__ == '__main__':
    app.run(debug=True)
