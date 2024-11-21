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
    return send_from_directory('templates', 'index.html')

@app.route('/about')
def about():
    return send_from_directory('templates', 'about.html')


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


# Routes for Top Songs
@app.route('/top-songs-long_term')
def top_songs_year():
    return top_songs('long_term')


@app.route('/top-songs-medium_term')
def top_songs_6_months():
    return top_songs('medium_term')


@app.route('/top-songs-short_term')
def top_songs_1_month():
    return top_songs('short_term')


# Routes for Top Artists
@app.route('/top-artists-long_term')
def top_artists_year():
    return top_artists('long_term')


@app.route('/top-artists-medium_term')
def top_artists_6_months():
    return top_artists('medium_term')


@app.route('/top-artists-short_term')
def top_artists_1_month():
    return top_artists('short_term')


@app.route('/top-songs-<time_range>')
def top_songs(time_range):
    tracks, user_name, time_range = get_top_items('songs', time_range)
    time_range_display = map_terms(time_range)
    return render_template('options.html', user_name=user_name, tracks=tracks, time_range=time_range_display)


@app.route('/top-artists-<time_range>')
def top_artists(time_range):
    artists, user_name, time_range = get_top_items('artists', time_range)
    time_range_display = map_terms(time_range)
    return render_template('options.html', user_name=user_name, artists=artists, time_range=time_range_display)


def get_top_items(type, time_range):
    sp = instance_creator()

    if type == 'songs':
        # Get the top tracks for the specified time range
        top_items = sp.current_user_top_tracks(limit=10, time_range=time_range)
        items = []
        for track in top_items['items']:
            items.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album_art': track['album']['images'][1]['url']  # Grab the second image size (medium size)
            })
    elif type == 'artists':
        # Get the top artists for the specified time range
        top_items = sp.current_user_top_artists(limit=10, time_range=time_range)
        items = []
        for artist in top_items['items']:
            items.append({
                'name': artist['name'],
                'genre': artist['genres'][0] if artist['genres'] else 'N/A',  # Get the first genre, if available
                'image': artist['images'][0]['url'] if artist['images'] else 'default_image_url.jpg'  # Get the first image (if available)
            })

    user = sp.current_user()
    user_name = user['display_name']

    return items, user_name, time_range


def map_terms(time_range):
    time_range_display = {
        'long_term': 'All Time',
        'medium_term': '6 Months',
        'short_term': '1 Month'
    }.get(time_range, 'All Time') #default

    return time_range_display
        

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

def create_spotify_oauth():

    return SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri = url_for('redirect_page', _external=True),
        scope='user-top-read user-read-recently-played'
    )

app.run(debug=True)