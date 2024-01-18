from .message import Message
from secure.hash import hash_str
from errors import UserError, InternalError
from flask import Blueprint, render_template, request, session, abort, url_for, redirect, current_app

user = Blueprint("user", __name__, template_folder='templates')


@user.route("/")
@user.route("/signup/")
@user.route("/signup", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        try:
            new_user = current_app.user_controller.create_user(
                name := request.form.get("name", ""),
                password := request.form.get("password", ""),
                request.form.get("confirm", ""))

            if not new_user:
                return render_template(
                    "signup.html",
                    message=Message("Exception", "Unknown Exception occurred while creating user."))
            else:
                if token := current_app.auth.authenticate_user(name, password, True):
                    session["token"] = token
                    return redirect(url_for("poll.view_all"))
                else:
                    abort(401)  # unauthorised
        except UserError as e:
            return render_template("signup.html", message=Message("warning", e))
        except Exception as e:
            raise e
    else:
        return render_template("signup.html")


@user.route("/login/")
@user.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = current_app.auth.authenticate_user(
            request.form.get("name", ""),
            request.form.get("password", ""),
            current_app.logger)

        if token:
            current_app.logger.info("token")
            session["token"] = token
            return redirect(url_for("poll.view_all"))
        else:
            return render_template(
                "login.html",
                message=Message("Exception", "Invalid username or password."))
    else:
        return render_template("login.html")


@user.route("/settings/")
@user.route("/settings", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        usr = current_app.user_controller.get_user(password=hash_str(request.form.get("current", "")))

        if usr:
            try:
                current_app.user_controller.update_user_password(
                    usr.id,
                    request.form.get("new", ""),
                    request.form.get("confirm", ""))
                return redirect(url_for("user.logout"))
            except Exception as e:
                return render_template("settings.html", message=Message("warning", e))
        else:
            return "Unknown Errror"
    else:
        return render_template("settings.html")


@user.route("/logout/")
@user.route("/logout")
def logout():
    session["token"] = ""
    return redirect(url_for("user.login"))
