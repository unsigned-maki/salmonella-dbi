import os
import config
import controllers
from views.poll import poll
from views.user import user
from secure.auth import Auth
from database import connection
from logging.config import dictConfig
from flask import Flask, request, session, redirect, url_for

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


app = Flask(__name__, static_url_path="/static")

app.secret_key = os.getenv("SESSION_SECRET")

app.register_blueprint(poll, url_prefix="/poll")
app.register_blueprint(user, url_prefix="/user")

app.connection = connection.MongoConnection()

app.user_controller = controllers.UserControllerMongo(app.connection)
app.poll_controller = controllers.PollControllerMongo(app.connection, app.user_controller)

app.auth = Auth(app.user_controller, app.logger)

@app.before_request
def require_auth():
    if request.endpoint in config.REQUIRE_AUTHENTICATION:
        if not app.auth.is_authenticated(session):
            app.logger.info(f"User {request.remote_addr} tried to access {request.endpoint} without being authenticated.")
            return redirect(url_for("user.login"))


@app.before_request
def no_auth():
    if request.endpoint in config.NO_AUTHENTICATION:
        if app.auth.is_authenticated(session):
            return redirect(url_for("poll.view_all"))


@app.route("/")
def index():
    return redirect(url_for("poll.view_all"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
