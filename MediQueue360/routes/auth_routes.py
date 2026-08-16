from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user

from database.db import get_db_connection
from models.user_model import User


auth = Blueprint("auth", __name__)

bcrypt = Bcrypt()


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:

            flash(
                "Please enter your email and password.",
                "warning"
            )

            return redirect(url_for("auth.login"))


        connection = get_db_connection()

        if connection is None:

            flash(
                "Unable to connect to the database.",
                "danger"
            )

            return redirect(url_for("auth.login"))


        cursor = connection.cursor(dictionary=True)


        try:

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )

            user_data = cursor.fetchone()


            if user_data is None:

                flash(
                    "Invalid email or password.",
                    "danger"
                )

                return redirect(url_for("auth.login"))


            if user_data["status"] != "active":

                flash(
                    "Your account is inactive.",
                    "warning"
                )

                return redirect(url_for("auth.login"))


            if not bcrypt.check_password_hash(
                user_data["password"],
                password
            ):

                flash(
                    "Invalid email or password.",
                    "danger"
                )

                return redirect(url_for("auth.login"))


            user = User(
                user_data["user_id"],
                user_data["full_name"],
                user_data["email"],
                user_data["password"],
                user_data["phone"],
                user_data["role"],
                user_data["status"],
                user_data["created_at"]
            )

            login_user(user)

            if user.role == "patient":

                return redirect(
                    url_for("patient.dashboard")
                )


            if user.role == "admin":

                return redirect(
                    url_for("admin.dashboard")
                )


            if user.role == "doctor":

                return redirect(
                    url_for("doctor.dashboard")
                )


            if user.role == "receptionist":

                return redirect(
                    url_for("receptionist.dashboard")
                )

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("home")
            )


        finally:

            cursor.close()
            connection.close()


    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        date_of_birth = request.form.get(
            "date_of_birth"
        )

        gender = request.form.get(
            "gender"
        )

        address = request.form.get(
            "address",
            ""
        ).strip()

        emergency_contact = request.form.get(
            "emergency_contact",
            ""
        ).strip()


        if not full_name or not email or not password:

            flash(
                "Please fill in all required fields.",
                "warning"
            )

            return redirect(
                url_for("auth.register")
            )


        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )


        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "warning"
            )

            return redirect(
                url_for("auth.register")
            )


        connection = get_db_connection()

        if connection is None:

            flash(
                "Unable to connect to the database.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )


        cursor = connection.cursor()


        try:

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )

            existing_user = cursor.fetchone()


            if existing_user:

                flash(
                    "An account with this email already exists.",
                    "warning"
                )

                return redirect(
                    url_for("auth.register")
                )


            hashed_password = bcrypt.generate_password_hash(
                password
            ).decode("utf-8")


            cursor.execute(
                """
                INSERT INTO users
                (
                    full_name,
                    email,
                    password,
                    phone,
                    role,
                    status
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    full_name,
                    email,
                    hashed_password,
                    phone,
                    "patient",
                    "active"
                )
            )


            user_id = cursor.lastrowid


            cursor.execute(
                """
                INSERT INTO patients
                (
                    user_id,
                    date_of_birth,
                    gender,
                    address,
                    emergency_contact
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user_id,
                    date_of_birth if date_of_birth else None,
                    gender if gender else None,
                    address if address else None,
                    emergency_contact if emergency_contact else None
                )
            )


            connection.commit()


            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("auth.login")
            )


        except Exception:

            connection.rollback()

            flash(
                "Registration failed. Please try again.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )


        finally:

            cursor.close()
            connection.close()


    return render_template("register.html")


@auth.route("/logout")
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )