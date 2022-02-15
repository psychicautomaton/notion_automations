from __future__ import absolute_import, division, print_function
from trakt import Trakt
from notion.client import NotionClient
import requests
import logging
import os
import json
import six
from trakt.objects import Movie, Show
import re
from fractions import Fraction

#authorize with both TraktTV and notion
def authenticate():
    authorization = os.environ.get('AUTHORIZATION')

    if authorization:
        return json.loads(authorization)

    print('Navigate to: %s' % Trakt['oauth'].authorize_url(''))

    code = six.moves.input('Authorization code:')
    if not code:
        exit(1)

    authorization = Trakt['oauth'].token(code, '')
    if not authorization:
        exit(1)

    print('Authorization: %r' % authorization)
    return authorization

#credentials
id = "your-trakt-client-id-here"
secret = "your-trakt-client-secret-here"

url = 'your-notion-database-url-here'
token = "your-notion-token_v2-here"

#function to add trakt movies marked 'watched' to notion database
def add_movies(url, token, id, secret):
    client = NotionClient(token_v2=token)
    cv = client.get_collection_view(url)

    logging.basicConfig(level=logging.DEBUG)

    Trakt.configuration.defaults.client(id=id, secret=secret)
    Trakt.configuration.defaults.http(retry=True)
    Trakt.configuration.defaults.oauth.from_response(authenticate())

    #select watched movies
    watched = Trakt['sync/watched'].movies()
    #loop through watched movies
    for movie in watched.values():
        if type(movie) is Movie:
            #save data about movie in database row
            print("\t progress:", movie.progress)
            row = cv.collection.add_row()
            row.title = movie.title
            row.year = movie.year
            row.overview = movie.overview
            row.runtime = str(movie.runtime)
            row.type = "Movie"
            row.watched = "Yes"
            row.genres = movie.genres

#same as above (basically) but for tv shows
def add_tv(url, token, id, secret):
    client = NotionClient(token_v2=token)
    cv = client.get_collection_view(url)


    Trakt.configuration.defaults.client(id=id, secret=secret)
    Trakt.configuration.defaults.http(retry=True)
    Trakt.configuration.defaults.oauth.from_response(authenticate())

    watched = Trakt['sync/watched'].shows()
    tvshows = Trakt['shows']

    for tvshow in watched.values():
        if type(tvshow) is Show:
            print(tvshow)
            show = tvshow.to_dict()

            row = cv.collection.add_row()
            row.title = show['title']
            row.year = show['year']
            id = show['ids']['trakt']
            #additional info about episode and season
            last_ep = str(tvshows.last_episode(id))
            last_season = last_ep[10:12]
            last_episode = last_ep[13:15]

            row.last_watched_episode = int(last_episode)
            row.last_watched_season = int(last_season)
            seasons = tvshows.seasons(id)
            if "S00" in seasons:
                length = len(list(seasons))
                row.number_of_seasons = length - 1
            else:
                row.number_of_seasons = len(list(seasons))

            #calculate overall progress based on episodes per season
            progress = str(tvshows.progress_watched(id=id))
            progress = re.match(r"([^\s]+)", progress)
            progress = str(progress.group())
            #set pattern for fractional values
            fraction_pattern = re.compile(r"^(?P<num>[0-9]+)/(?P<den>[0-9]+)$")
            g = fraction_pattern.search(progress)
            if g:
                f = float(g.group("num"))/float(g.group("den"))
                row.progress = f
            if "genres" in show.keys():
                #save genre data if available
                row.genres = str(show['genres'])
            else:
                continue



#run both functions
add_tv(url, token, id, secret)
add_movies(url, token, id, secret)
