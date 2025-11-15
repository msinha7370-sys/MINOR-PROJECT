from flask import Flask, render_template, g, request, redirect, url_for, jsonify, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

DB_PATH = "tourism.db"
app = Flask(__name__)
app.config["DATABASE"] = DB_PATH
app.config["SECRET_KEY"] = "dev-secret"
# Simple admin credentials (change in production)
app.config['ADMIN_USER'] = 'admin'
app.config['ADMIN_PASS_HASH'] = generate_password_hash('admin123')

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# Decorator to require admin login
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in and if their user_id is 'admin'
        if session.get('user_id') != 'admin':
            flash('Admin access is required for this action.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Utility: fetch attractions
def fetch_attractions():
    db = get_db()
    cur = db.execute("SELECT * FROM attractions")
    return cur.fetchall()

def fetch_attraction(attraction_id):
    db = get_db()
    cur = db.execute("SELECT * FROM attractions WHERE id=?", (attraction_id,))
    return cur.fetchone()

# Utility: automatically calculate and update crowd percentage based on bookings
def calculate_and_update_crowd(attraction_id):
    """Calculate crowd % from total bookings and update the attraction"""
    db = get_db()
    
    # Get attraction's capacity
    attraction = fetch_attraction(attraction_id)
    if not attraction:
        return
    
    capacity = attraction['capacity'] or 100
    
    # Get total booked seats for this attraction
    cur = db.execute("SELECT SUM(seats) as total_seats FROM bookings WHERE attraction_id=?", (attraction_id,))
    result = cur.fetchone()
    total_seats = result['total_seats'] or 0
    
    # Calculate crowd percentage (cap at 100%)
    crowd_percentage = min(int((total_seats / capacity) * 100), 100)
    
    # Update the attraction's crowd level
    db.execute("UPDATE attractions SET crowd=? WHERE id=?", (crowd_percentage, attraction_id))
    db.commit()

# Home - list attractions and recommendations
@app.route("/")
def index():
    attractions = fetch_attractions()
    # new user preferences can be passed via query params; we'll read from ?prefs=tag1,tag2
    prefs = request.args.get("prefs", "")
    pref_list = [p.strip().lower() for p in prefs.split(",") if p.strip()]
    # simple recommendation: score by matching tags and rating and low crowd
    recs = []
    for a in attractions:
        tags = [t.strip().lower() for t in a['tags'].split(",")]
        match_count = sum(1 for t in tags if t in pref_list) if pref_list else 0
        # score: matches * 10 + rating*2 - crowd*0.1
        score = match_count*10 + (a['avg_rating'] or 0)*2 - (a['crowd'] or 0)*0.1
        recs.append((a, score))
    recs_sorted = sorted(recs, key=lambda x: x[1], reverse=True)
    recommendations = [r[0] for r in recs_sorted[:3]]
    return render_template("index.html", attractions=attractions, recommendations=recommendations, prefs=prefs)

# Attraction detail
@app.route("/attraction/<int:aid>")
def attraction(aid):
    a = fetch_attraction(aid)
    if not a:
        return "Not Found", 404
    return render_template("attraction.html", a=a)

# Bookings page
@app.route("/bookings", methods=["GET", "POST"])
def bookings():
    db = get_db()
    # Require login for booking
    if 'user_id' not in session:
        flash("Please login to view and make bookings.", "info")
        return redirect(url_for('login', next=url_for('bookings')))

    if request.method == "POST":
        # User is logged in, so we get their details from the session
        user_id = session['user_id']
        user_info = db.execute("SELECT name, email FROM users WHERE id = ?", (user_id,)).fetchone()
        name = user_info['name']
        email = user_info['email']
        attraction_id = int(request.form["attraction_id"])
        seats = int(request.form.get("seats", 1))
        db.execute("INSERT INTO bookings (name,email,attraction_id,seats,user_id) VALUES (?,?,?,?,?)",
                   (name, email, attraction_id, seats, user_id))
        db.commit()
        # Automatically update crowd percentage after booking
        calculate_and_update_crowd(attraction_id)
        return redirect(url_for("bookings"))
    cur = db.execute("SELECT b.*, a.name as attraction_name, a.crowd FROM bookings b LEFT JOIN attractions a ON b.attraction_id=a.id ORDER BY b.timestamp DESC")
    rows = cur.fetchall()
    attractions = fetch_attractions()
    return render_template("bookings.html", bookings=rows, attractions=attractions)

# Delete single booking
@app.route("/bookings/delete/<int:booking_id>", methods=["POST"])
@admin_required
def delete_booking(booking_id):
    db = get_db()
    cur = db.execute("SELECT attraction_id FROM bookings WHERE id=?", (booking_id,))
    booking = cur.fetchone()
    if booking:
        db.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        db.commit()
        # Recalculate crowd after deletion
        calculate_and_update_crowd(booking['attraction_id'])
    return redirect(url_for("bookings"))

# Clear all bookings
@app.route("/bookings/clear-all", methods=["POST"])
@admin_required
def clear_all_bookings():
    db = get_db()
    try:
        with db: # Use 'with db' to manage transactions automatically (commit/rollback)
            # First, get all attraction IDs that will be affected.
            cur = db.execute("SELECT DISTINCT attraction_id FROM bookings")
            attraction_ids = [row[0] for row in cur.fetchall()]

            # Now, delete all bookings.
            db.execute("DELETE FROM bookings")

            # After deletion, update the crowd levels for the affected attractions.
            if attraction_ids:
                db.execute("UPDATE attractions SET crowd = 0 WHERE id IN ({})".format(','.join('?' for _ in attraction_ids)), attraction_ids)
    except sqlite3.Error as e:
        flash(f"A database error occurred: {e}", "error")
    return redirect(url_for("bookings"))

# Admin view to see/update crowd levels manually
@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    db = get_db()
    if request.method == "POST":
        aid = int(request.form["attraction_id"])
        crowd = int(request.form["crowd"])
        db.execute("UPDATE attractions SET crowd=? WHERE id=?", (crowd, aid))
        db.commit()
        return redirect(url_for("admin"))
    attractions = fetch_attractions()
    return render_template("admin.html", attractions=attractions)


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or url_for('admin')
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()

        # Check if it's the admin
        if username == app.config['ADMIN_USER'] and check_password_hash(app.config['ADMIN_PASS_HASH'], password):
            session['user_id'] = 'admin' # Special value for admin
            session['username'] = app.config['ADMIN_USER']
            flash('Logged in successfully', 'success')
            return redirect(request.form.get('next') or url_for('admin'))

        # Check regular users
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(next_url or url_for('index'))

        flash('Invalid username or password', 'error')
    return render_template('login.html', next=next_url)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        # Check if user or email already exists
        if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            flash('Username already taken.', 'error')
        elif db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            flash('Email address already registered.', 'error')
        else:
            # Add new user
            hashed_password = generate_password_hash(password)
            db.execute("INSERT INTO users (username, name, email, password) VALUES (?, ?, ?, ?)",
                       (username, name, email, hashed_password))
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out', 'success')
    return redirect(url_for('index'))

# API: sensor endpoint (simulate IoT device posting crowd levels)
@app.route("/api/sensor", methods=["POST"])
def api_sensor():
    data = request.get_json() or {}
    aid = data.get("attraction_id")
    crowd = data.get("crowd")
    if aid is None or crowd is None:
        return jsonify({"status":"error","message":"attraction_id and crowd required"}), 400
    db = get_db()
    db.execute("UPDATE attractions SET crowd=? WHERE id=?", (int(crowd), int(aid)))
    db.commit()
    return jsonify({"status":"ok","attraction_id":aid,"crowd":crowd})

# API: get attraction status (for AJAX polling)
@app.route("/api/status/<int:aid>")
def api_status(aid):
    a = fetch_attraction(aid)
    if not a:
        return jsonify({"status":"error","message":"not found"}), 404
    return jsonify({
        "id": a["id"],
        "name": a["name"],
        "crowd": a["crowd"],
        "avg_rating": a["avg_rating"],
        "image_url": a["image_url"]
    })

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Database not found at '{DB_PATH}'. Please run the init_db.py script first to create it.")
        # Exit the application to prevent it from running in a broken state.
        exit(1)
    app.run(debug=True)
