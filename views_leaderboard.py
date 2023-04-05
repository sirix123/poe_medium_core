import os
import random
import string
from urllib.parse import urlencode

import pandas as pd
import requests
from flask import render_template, request, redirect
from passlib.hash import sha256_crypt

# import all classes
from app.models.model import *
# importing blueprint from __init__.py
from . import poe_leaderboard

@poe_leaderboard.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@poe_leaderboard.route('/index')
@poe_leaderboard.route('/')
def index():
    return render_template("poe_leaderboard/index.html")

@poe_leaderboard.route('/about')
def poe_about(): 
    return render_template("poe_leaderboard/index.html")

@poe_leaderboard.route('/poe_leaderboard')
def overall_leaderboard():
    sql_query = pd.read_sql('character', os.environ.get('SQLALCHEMY_DATABASE_URI'))
    df = pd.DataFrame(sql_query, columns = ['account', 'clean_character_name','class_poe','level', 'league','experience'])
    df = df.sort_values(by='experience', ascending=False)
    # characters = Character.retrieve_character_entries()    
    return render_template("poe_leaderboard/index.html",characters=df.to_html(classes="table"))

@poe_leaderboard.route('/poe_leaderboard_current_league')
def current_league():
    sql_query = pd.read_sql('character', os.environ.get('SQLALCHEMY_DATABASE_URI'))
    df = pd.DataFrame(sql_query, columns = ['account', 'clean_character_name', 'class_poe' ,'level', 'league','experience'])
    df = df[df['league'].str.contains("Crucible")]
    df = df.sort_values(by='experience', ascending=False)

    return render_template("poe_leaderboard/index.html",characters=df.to_html(classes="table"))

@poe_leaderboard.route('/poe_leaderboard_medium_core_league')
def medium_core():
    sql_query = pd.read_sql('character', os.environ.get('SQLALCHEMY_DATABASE_URI'))
    df = pd.DataFrame(sql_query, columns = ['account', 'clean_character_name', 'class_poe' ,'level','deaths','league','experience'])
    medium_core_league_name = os.environ.get('POE_MEDIUM_CORE_LEAGUE_NAME')
    df = df[df['league'].str.contains(medium_core_league_name)]
    df = df.sort_values(by='experience', ascending=False)

    return render_template("poe_leaderboard/index.html",characters=df.to_html(classes="table"))

@poe_leaderboard.route('/poe_leaderboard_app_install')
def app_install():
    state_length = 10
    state = sha256_crypt.hash(get_random_string(state_length))

    poe_auth_url = "https://www.pathofexile.com/oauth/authorize" + "?" + urlencode({
        'client_id': os.environ.get('OAUTH_CREDENTIALS_ID'),
        'response_type': 'code',
        'scope': 'account:profile account:characters',
        'state': state,
        'redirect_uri': "https://www.sdgames.co/OG/callback",
        'prompt': 'consent'
    })
    return redirect(poe_auth_url, code=302)

@poe_leaderboard.route('/callback')
def callback():
    state = request.args.get('state')
    code = request.args.get('code')

    url_token = 'https://www.pathofexile.com/oauth/token?'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent' : 'OAuth '+os.environ.get('OAUTH_CREDENTIALS_ID')+'/1.0.0 (contact: stefan@sdgames.co) StrictMode'
    }
    payload = {
        'client_id': os.environ.get('OAUTH_CREDENTIALS_ID'),
        'client_secret': os.environ.get('OAUTH_CREDENTIALS_SECRET'),
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': "https://www.sdgames.co/OG/callback",
        'scope': 'account:profile account:characters'
    }

    #  get access token
    response_access_token = requests.post(url_token, data=payload, headers=headers)
    if response_access_token.status_code == 200:
        data = response_access_token.json()
    else:
        print("--------------------")
        for key, value in response_access_token.headers.items():
            print(key, str(value))
        print("--------------------")
        if "token-request-limit" in response_access_token.headers:
            return "1.1: Error " + str(response_access_token.status_code) + " you're resquesting tokens too fast, wait a while"
        return '1: Error ' + str(response_access_token.status_code)

    access_token = data['access_token']
    access_token_expiry = data['expires_in']

    url_profile = 'https://api.pathofexile.com/profile'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'User-Agent' : 'OAuth '+os.environ.get('OAUTH_CREDENTIALS_ID')+'/1.0.0 (contact: stefan@sdgames.co) StrictMode'
    }
    response_profile = requests.get(url_profile, headers=headers)

    if response_profile.status_code == 200:
        profile_data = response_profile.json()
    else:
        return '2: Error ' + str(response_profile.status_code)

    # get account name
    account_name = profile_data['name']

    # create account or update db details for account name
    if UserOG.check_og_poe_userbase(account_name):
        UserOG.update_access_token_for_user(account_name, access_token)
    else:
        UserOG.create_og_poe_user(account_name, access_token)

    return redirect("https://www.sdgames.co/OG/poe_leaderboard", code=302)

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
