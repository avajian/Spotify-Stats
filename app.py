# import necessary modules
import time
import os
import spotipy
import logging
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, send_from_directory, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()  # This loads the .env file

app = Flask(__name__)
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_random_default_key')
TOKEN_INFO = 'token_info'


# routes

@app.route('/')
def home():
    return send_from_directory('', 'index.html')

@app.route('/about')
def about():
    return send_from_directory('', 'about.html')


@app.route('/login')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)


@app.route('/logout')
def logout():
    # remove the token info
    session.clear()
     # Redirect the user to Spotify's logout URL
    spotify_logout_url = 'https://www.spotify.com/logout'
    return redirect(f"{spotify_logout_url}?redirect_uri={url_for('home', _external=True)}")


@app.route('/redirect')
def redirect_page():
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info

    sp = instance_creator()
    user = sp.current_user()
    user_name = user['display_name']
    return render_template('options.html', user_name=user_name, _external=True)


@app.route('/options')
def options():
    return send_from_directory('templates', 'options.html')


@app.route('/top-songs-long_term')
def top_songs_year():
    tracks = top_songs(time_range='long_term')  # 'long_term' for the past several years
    return tracks


@app.route('/top-songs-medium_term')
def top_songs_6_months():
    tracks = top_songs(time_range='medium_term')  # 'medium_term' for the past 6 months
    return tracks


@app.route('/top-songs-short_term')
def top_songs_1_month():
    tracks = top_songs(time_range='short_term')  # 'short_term' for the past month
    return tracks


@app.route('/top-songs-<time_range>')
def top_songs(time_range):
    sp = instance_creator()

    # Get the top tracks for the specified time range
    top_tracks = sp.current_user_top_tracks(limit=10, time_range=time_range)

    tracks = []
    for track in top_tracks['items']:
        tracks.append({
            'name': track['name'],
            'artist': track['artists'][0]['name']
        })

    user = sp.current_user()
    user_name = user['display_name']

    return render_template('options.html', user_name=user_name, tracks=tracks)  # Pass tracks to template



def instance_creator():
    # get token and create spotipy instance
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    return sp

# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

logging.basicConfig(level=logging.DEBUG)

def create_spotify_oauth():

    return SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri = url_for('redirect_page', _external=True),
        scope='user-top-read user-read-recently-played'
    )

app.run(debug=True)