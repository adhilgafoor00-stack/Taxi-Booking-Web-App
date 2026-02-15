from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taxi.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- DATABASE MODELS ---------------- #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))  # user or driver

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pickup = db.Column(db.String(200))
    drop = db.Column(db.String(200))
    distance = db.Column(db.Float)
    fare = db.Column(db.Float)
    status = db.Column(db.String(20), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    driver_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed_pw = generate_password_hash(request.form["password"])
        new_user = User(
            name=request.form["name"],
            email=request.form["email"],
            password=hashed_pw,
            role=request.form["role"]
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registered Successfully!")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            if user.role == "driver":
                return redirect(url_for("driver_dashboard"))
            return redirect(url_for("dashboard"))
        flash("Invalid Credentials")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", bookings=bookings)

@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "POST":
        distance = float(request.form["distance"])
        fare = 50 + (distance * 10)  # Fare Logic

        new_booking = Booking(
            pickup=request.form["pickup"],
            drop=request.form["drop"],
            distance=distance,
            fare=fare,
            user_id=current_user.id
        )
        db.session.add(new_booking)
        db.session.commit()
        flash("Ride Booked Successfully!")
        return redirect(url_for("dashboard"))
    return render_template("book.html")

@app.route("/driver")
@login_required
def driver_dashboard():
    bookings = Booking.query.filter_by(status="Pending").all()
    return render_template("driver.html", bookings=bookings)

@app.route("/accept/<int:id>")
@login_required
def accept(id):
    booking = Booking.query.get(id)
    booking.status = "Accepted"
    booking.driver_id = current_user.id
    db.session.commit()
    return redirect(url_for("driver_dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
