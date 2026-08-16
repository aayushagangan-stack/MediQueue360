from functools import wraps

from flask import session, redirect, url_for, flash


def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login to continue.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


def role_required(required_role):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            if "user_id" not in session:

                flash(
                    "Please login to continue.",
                    "warning"
                )

                return redirect(
                    url_for("auth.login")
                )


            if session.get("role") != required_role:

                flash(
                    "You do not have permission to access this page.",
                    "danger"
                )

                return redirect(
                    url_for("auth.login")
                )


            return function(
                *args,
                **kwargs
            )

        return wrapper

    return decorator