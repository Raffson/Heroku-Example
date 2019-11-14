import json

from flask import Flask, render_template, request, redirect, url_for, make_response
from requests_oauthlib import OAuth2Session
import os

try:
    import secrets  # only needed for localhost, that's why it's in the try/except statement
except ImportError as e:
    pass

app = Flask(__name__)


def is_local():
    with app.test_request_context("/"):
        root_url = str(request.url_root)
        developer_url = "http://127.0.0.1/"
        developer_url2 = "http://localhost/"
        developer_url3 = "http://0.0.0.0/"
        return root_url == developer_url or root_url == developer_url2 or root_url == developer_url3


local = is_local()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/github/login")
def github_login():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"))  # prepare the GitHub OAuth session
    authorization_url, state = github.authorization_url("https://github.com/login/oauth/authorize")  # GitHub authorization URL

    response = make_response(redirect(authorization_url))  # redirect user to GitHub for authorization
    response.set_cookie("oauth_state", state, httponly=True, samesite='Strict')  # for CSRF purposes

    return response


@app.route("/github/callback")
def github_callback():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), state=request.cookies.get("oauth_state"))
    token = github.fetch_token("https://github.com/login/oauth/access_token",
                               client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
                               authorization_response=request.url)

    response = make_response(redirect(url_for('profile')))  # redirect to the profile page
    if local:
	print("Not working properly!")
        response.set_cookie("oauth_token", json.dumps(token), httponly=True)
    else:
	print("Working properly...")
        response.set_cookie("oauth_token", json.dumps(token), httponly=True, samesite='Strict')

    return response


@app.route("/profile")
def profile():
    github = OAuth2Session(os.environ.get("GITHUB_CLIENT_ID"), token=json.loads(request.cookies.get("oauth_token")))
    github_profile_data = github.get('https://api.github.com/user').json()

    return render_template("profile.html", github_profile_data=github_profile_data)


@app.route("/github/logout")
def logout():
    response = make_response(redirect(url_for('index')))  # redirect to the index page
    response.set_cookie("oauth_token", expires=0)  # delete the oauth_cookie to logout

    return response


if __name__ == '__main__':
    app.run()
