from flask import Flask, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =========================
# DATABASE MODELS
# =========================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))  # user or driver
    phone = db.Column(db.String(20))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    driver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    pickup = db.Column(db.String(200))
    drop = db.Column(db.String(200))
    distance = db.Column(db.Float)
    fare = db.Column(db.Float)

    status = db.Column(db.String(50), default="Pending")

    user = db.relationship("User", foreign_keys=[user_id])
    driver = db.relationship("User", foreign_keys=[driver_id])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return redirect("/login")


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        phone = request.form.get("phone")

        if not all([name, email, password, role, phone]):
            flash("All fields are required.")
            return redirect("/register")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.")
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            phone=phone
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully! Please login.")
        return redirect("/login")

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect("/dashboard")

        flash("Invalid email or password.")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "driver":
        bookings = Booking.query.filter_by(status="Pending").all()
        return render_template("driver.html", bookings=bookings)

    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", bookings=bookings)


# BOOK RIDE
@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "POST":

        pickup = request.form.get("pickup")
        drop = request.form.get("drop")
        distance_value = request.form.get("distance")

        if not pickup or not drop or not distance_value:
            flash("Please select pickup and drop locations on the map.")
            return redirect("/book")

        try:
            distance = float(distance_value)
        except ValueError:
            flash("Invalid distance value.")
            return redirect("/book")

        fare = distance * 10  # ₹10 per km

        booking = Booking(
            user_id=current_user.id,
            pickup=pickup,
            drop=drop,
            distance=distance,
            fare=fare
        )

        db.session.add(booking)
        db.session.commit()

        flash("Ride booked successfully!")
        return redirect("/dashboard")

    return render_template("book.html")


# DRIVER ACCEPT RIDE
@app.route("/accept/<int:id>")
@login_required
def accept(id):

    if current_user.role != "driver":
        flash("Access denied.")
        return redirect("/dashboard")

    booking = Booking.query.get_or_404(id)

    booking.status = "Accepted"
    booking.driver_id = current_user.id

    db.session.commit()

    flash("Ride accepted successfully!")
    return redirect("/dashboard")


# =========================
# CREATE DATABASE
# =========================

with app.app_context():
    db.create_all()


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
