from bs4 import BeautifulSoup
import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sqlite3
import matplotlib.pyplot as plt
import pandas


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="46971f74951f4e849522c6763fea7f0a",
                                               client_secret="53c9fc273d0b4507a65eafd4cc148d0f",
                                               redirect_uri="https://sites.google.com/umich.edu/meport/home"))


CACHE_FILENAME = "cache.json"


class Song:
    '''a song

    Instance Attributes
    -------------------
    
    title: string
        the title of the song 
        ex: "All I Want for Christmas is You"
    
    artist: string
        the artist or artists who performed the song
        ex: "Mariah Carey"
    
    holnum: integer
        the position the song object holds on the holiday hot 100 chart
        can be any number 1-100
        
    '''
    def __init__(self, title, artist, holnum):

        self.title = title
        self.artist = artist
        self.holnum = holnum
pass


def get_songs(board_url):
    ''' appends song instance items to the "song_lists" list from the holiday hot 100, in order 1-100.

    Parameters
    ----------
    board_url: string
        the url for the holiday hot 100 chart
        creators note: other charts have different html formatting, so only works with holiday chart for now

    Returns
    -------
    None
    
    '''
    print("Fetching latest Holiday Hot 100")
    boardpage = requests.get(board_url)
    boardsoup = BeautifulSoup(boardpage.text, "html.parser")
    find_song_details = boardsoup.find_all(class_= "item-details")
    for song_raw in find_song_details:
        song = Song(title = song_raw.find(class_="item-details__title").get_text(), artist = song_raw.find(class_ = "item-details__artist").get_text(), holnum = find_song_details.index(song_raw) + 1)
        songs_list.append(song)
    pass


def load_cache():
    ''' opens cache (json file specified above) and reads the data for use

    Parameters
    ----------
    None

    Returns
    -------
    None
    
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    ''' opens cache (json file specified above) and writes information in as a dictionary

    Parameters
    ----------
    None

    Returns
    -------
    None
    
    '''
    cache_file = open(CACHE_FILENAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def get_spotify_data(song_list):
    ''' sends song information from song instances to spotify search API, recieves JSONs of song information back
    caches JSONs for future use: key is the 11th song instance's title, as 11th place has more fluctuation than top 10.
    takes spotify's internal popularity number from JSON and appends that to the "spotify_popularity_list" list
    if song is not available on spotify, it does not have a popularity score, thus resulting in a null value being added

    Parameters
    ----------
    song_list: list
        list of song instances created from the info in the holiday hot 100 chart

    Returns
    -------
    None
    
    '''
    spotify_json_list= []
    if song_list[11].title not in board_dict.keys():
        print("Fetching Spotify Data")
        for song in song_list:
            song_title = str(song.title)
            song_artist = str(song.artist)
            results = sp.search(q ="track:" + song_title + " artist:" + song_artist, limit = 1, type = "track", market= None, )
            spotify_json_list.append(results)
        board_dict[song_list[11].title] = spotify_json_list
        save_cache(board_dict)
    else:
        print("Using cache for Spotify Data")
        spotify_json_list = board_dict[song_list[11].title]
    for song in spotify_json_list:
        try:
            spotify_popularity_list.append(song["tracks"]["items"][0]["popularity"])
        except:
            spotify_popularity_list.append("Null")
    pass


def combine_list(spot_list, hot_list):

    ''' takes list of song instances and list of spotify popularity and combines them by appending them to spot_hot_list
    for use of matplotlib and sqlite3

    Parameters
    ----------
    spot_list: list
        list of spotify popularity number ordered by hot 100 holiday chart position 1-100
    
    hot_list: list
        list of song instances, containing the titles, artists and hot 100 positions of all 100 songs on hot 100 holiday chart.

    Returns
    -------
    None
    
    '''
    for song in hot_list:
        spot_hot_list.append((song.title, song.artist, song.holnum, spot_list[hot_list.index(song)]))
    pass


def create_table():
    ''' creates table in sqlite document with columns for title, artist, hot 100 position, and spotify popularity score

    Parameters
    ----------
    None

    Returns
    -------
    None
    
    '''
    conn = sqlite3.connect("spot_hot.sqlite")
    c = conn.cursor()
    c.execute('''CREATE TABLE spothot
                (title text, artist text, hot100position integer, spotifypopularityscore integer)''')
    pass


def insert_rows(spothotlist):
    ''' inserts rows of data into the spothot table in the spot_hot.sqlite file from the combined list "spot_hot_list"

    Parameters
    ----------
    spothotlist: list
        list containing title, artist, hot 100 position and spotify popularity score

    Returns
    -------
    None
    
    '''
    conn = sqlite3.connect("spot_hot.sqlite")
    conn.executemany('''INSERT INTO spothot (title, artist, hot100position, spotifypopularityscore) VALUES (?, ?, ?, ?)''', spot_hot_list)
    conn.commit()
    pass


def execute_scatterplot(spothotlist):
    ''' creates scatterplot of hot 100 position vs spotify popularity score
    generates lists of x points and y points from the "spot_hot_list", a list of lists in which index [2] is hot 100 score and index [3] is spotify score
    note that some songs are not available on spotify, and try: except: removes data points with a null value for spotify popularity score

    Parameters
    ----------
    spothotlist: list
        list containing title, artist, hot 100 position and spotify popularity score

    Returns
    -------
    plt.show(): function
        shows scatterplot created by functions above in matlib
    
    '''
    print("Setting up scatterplot...")
    exes = []
    wys = []
    for song in spothotlist:
        try:
            wys.append(int(song[3]))
            exes.append(int(song[2]))    
        except:
            pass

    plt.scatter(exes, wys, label = 'Hot 100 vs Spotify Score')
    plt.xlabel("Hot 100 (1 = most popular, 100 = least popular)")
    plt.ylabel("Spotify Popularity Score (1 = least popular, 100 = most popular)")
    return plt.show()


def display_info():
    ''' displays SQL queries for 1/4 of the data at a time in the pandas data frame 
    starting with 1-25, ending 75-100 if requested by entering "next". any other entry will exit out of the program.

    Parameters
    ----------
    None

    Returns
    -------
    None
    
    '''
    conn = sqlite3.connect("spot_hot.sqlite")
    print("Printing data for top 25...")
    counter = 1
    while counter > 0:
        print(pandas.read_sql_query('''SELECT hot100position, title, artist, spotifypopularityscore FROM spothot WHERE hot100position < 26''', conn))
        prompt = input("To see next 25 songs, type next. Any other input will result in quitting the program. ")
        if prompt.lower() == "next":
            print(pandas.read_sql_query('''SELECT hot100position, title, artist, spotifypopularityscore FROM spothot WHERE hot100position BETWEEN 26 and 50''', conn))
            prompt2 = input("To see next 25 songs, type next. Any other input will result in quitting the program. ")
            if prompt2.lower() == "next":
                print(pandas.read_sql_query('''SELECT hot100position, title, artist, spotifypopularityscore FROM spothot WHERE hot100position BETWEEN 51 and 75''', conn))
                prompt3 = input("To see next 25 songs, type next. Any other input will result in quitting the program. ")
                if prompt3.lower() == "next":
                    print(pandas.read_sql_query('''SELECT hot100position, title, artist, spotifypopularityscore FROM spothot WHERE hot100position BETWEEN 75 AND 100''', conn))
                    prompt4 = input("To go back to the beginning, type restart. Any other input will result in quitting the program. ")
                    if prompt4.lower() == "restart":
                        continue
                    else: 
                        counter = 0
                else:
                    counter = 0
            else: 
                counter = 0
        else:
            counter = 0
    pass




board_dict = load_cache()
songs_list = []
spotify_popularity_list = []
spot_hot_list = []

if __name__ == "__main__":
    get_songs("https://www.billboard.com/charts/hot-holiday-songs")
    get_spotify_data(songs_list)
    combine_list(spotify_popularity_list, songs_list)
    try:
        create_table()
        insert_rows(spot_hot_list)
    except:
        conn = sqlite3.connect("spot_hot.sqlite")
        conn.execute('''DROP TABLE spothot''')
        create_table()
        insert_rows(spot_hot_list)
    execute_scatterplot(spot_hot_list)
    display_info()