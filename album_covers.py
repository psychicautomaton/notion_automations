#import libraries
from notion.client import NotionClient
from pocket import Pocket
import requests
from bs4 import BeautifulSoup
import urllib.request
import shutil
import schedule
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotify_images

#notion credentials
token = ""
#database link for music
url = ""

#spotify playlist details
id = ""
secret = ""
playlist_id = ''

#write function to create a notion database of all the songs in a playlist
#that contains track name, album name, album cover image, and artist name
def get_covers(token, url, id, secret, playlist_id):
    client = NotionClient(token_v2=token)
    cv = client.get_collection_view(url)
    result = cv.default_query().execute()

    client_credentials_manager = SpotifyClientCredentials(client_id=id, client_secret=secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


    playlist = sp.user_playlist("umusings2", playlist_id)
    for item in playlist['tracks']['items']:
        row = cv.collection.add_row()
        print("\n",item)
        album_nest = item['track']['album']
        album = album_nest['name']
        artist_nest = album_nest['artists'][0]
        artist = artist_nest['name']
        track_nest = item['track']
        track = track_nest['name']
        images = album_nest['images'][0]
        image = images['url']
        row.song = track
        row.image = image
        row.album = album
        row.artist = artist

#run function
get_covers(token, url, id, secret, playlist_id)
