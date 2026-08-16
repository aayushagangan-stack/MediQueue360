import os


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "mediqueue360-secret-key"
    )

    MYSQL_HOST = os.environ.get(
        "MYSQL_HOST",
        "localhost"
    )

    MYSQL_USER = os.environ.get(
        "MYSQL_USER",
        "root"
    )

    MYSQL_PASSWORD = os.environ.get(
        "MYSQL_PASSWORD",
        "......"
    )

    MYSQL_DATABASE = os.environ.get(
        "MYSQL_DATABASE",
        "mediqueue360"
    )
