from flask import Flask, render_template

from flask_login import LoginManager

from config import Config

from database.db import get_db_connection
from models.user_model import User

from routes.auth_routes import auth
from routes.patient_routes import patient
from routes.doctor_routes import doctor
from routes.receptionist_routes import receptionist
from routes.admin_routes import admin


app = Flask(__name__)

import os

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "uploads"
)

app.config.from_object(Config)


login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):

    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        user_data = cursor.fetchone()

        if user_data is None:
            return None

        return User(
            user_data["user_id"],
            user_data["full_name"],
            user_data["email"],
            user_data["password"],
            user_data["phone"],
            user_data["role"],
            user_data["status"],
            user_data["created_at"]
        )

    finally:

        cursor.close()
        connection.close()


@app.route("/")
def home():

    return render_template(
        "index.html"
    )


app.register_blueprint(
    auth
)

app.register_blueprint(
    patient
)

app.register_blueprint(
    doctor
)

app.register_blueprint(
    receptionist
)

app.register_blueprint(
    admin
)


if __name__ == "__main__":

    app.run(
        debug=True
    )