import sse
import uuid
from .message import Message
from mongoengine import ValidationError
from flask import Blueprint, render_template, request, session, Response, abort, redirect, url_for, make_response, current_app

poll = Blueprint('poll', __name__, template_folder='templates')


@poll.route("/view/<id>/")
@poll.route("/view/<id>")
def view(id):
    if not (pl := current_app.poll_controller.get_poll(id=uuid.UUID(id))):
        abort(404)  # not found

    if (chart := request.args.get("chart", "")) not in ["bar", "doughnut", "pie"]:
        chart = "bar"

    return render_template(
        "poll.html",
        logged_in=current_app.auth.is_authenticated(session),
        poll=pl,
        chart=chart)


@poll.route("/")
@poll.route("/view/")
@poll.route("/view")
def view_all():
    polls = current_app.poll_controller.get_polls(author=current_app.auth.get_user(session).id)
    return render_template("overview.html", polls=polls, poll_count=len(polls))


@poll.route("/vote/<id>/")
@poll.route("/vote/<id>", methods=["GET", "POST"])
def vote(id):
    if not (pl := current_app.poll_controller.get_poll(id=uuid.UUID(id))):
        abort(404)  # not found

    if request.cookies.get(pl.id.hex):
        return redirect(url_for("poll.view", id=id))

    author = current_app.user_controller.get_user(id=pl.author)

    if request.method == "POST":
        if current_app.auth.is_authenticated(session) and author:
            if author.id == current_app.auth.get_user(session).id:
                return render_template(
                    "vote.html",
                    logged_in=current_app.auth.is_authenticated(session),
                    poll=pl,
                    author=author.name if author else "Deleted User",
                    message=Message("error", "You must not vote on your own poll."))

        if len(request.form) != 1:
            return render_template(
                "vote.html",
                logged_in=current_app.auth.is_authenticated(session),
                poll=pl,
                author=author.name if author else "Deleted User",
                message=Message("warning", "No option was selected."))

        choice = list(request.form)[0]

        if not current_app.poll_controller.increment_option(uuid.UUID(choice)):
            return render_template(
                "vote.html",
                logged_in=current_app.auth.is_authenticated(session),
                poll=pl,
                author=author.name if author else "Deleted User",
                message=Message("error", "Something went wrong selecting your option."))
        else:
            resp = make_response(redirect(url_for("poll.view", id=id)))
            resp.set_cookie(pl.id.hex, "true")
            return resp
    else:
        return render_template(
            "vote.html",
            logged_in=current_app.auth.is_authenticated(session),
            poll=pl,
            author=author.name if author else "Deleted User")


@poll.route("/create/")
@poll.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        options = []

        for field in request.form:
            if "option" in field:
                options.append(request.form[field])

        try:
            poll = current_app.poll_controller.create_poll(
                current_app.auth.get_user(session).id,
                options,
                request.form.get("title"),
                request.form.get("desc"))

            if poll:
                return redirect(url_for("poll.view_all"))
            else:
                return render_template(
                    "signup.html",
                    message=Message("error", "Unknown error occurred while creating poll."))

        except ValidationError as e:
            return render_template("create.html", message=Message("warning", e))
    else:
        return render_template("create.html")


@poll.route("/delete/<id>/")
@poll.route("/delete/<id>")
def delete(id):
    if not (pl := current_app.poll_controller.get_poll(id=uuid.UUID(id))):
        abort(404)  # not found

    if pl.author != current_app.auth.get_user(session).id:
        abort(401)  # unauthorised

    current_app.logger.info(str(pl.id))
    current_app.poll_controller.delete_poll(pl.id)
    return redirect(url_for("poll.view_all"))


@poll.route("/listen/<id>", methods=["GET"])
def listen(id):

    def stream():
        messages = sse.announcer.listen()
        while True:
            msg = messages.get()
            if id in msg:
                yield sse.format("update")

    return Response(stream(), mimetype="text/event-stream")
