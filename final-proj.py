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
    def __init__(self, title, artist, holnum):
        self.title = title
        self.artist = artist
        self.holnum = holnum
    def __str__(self):
        return self.title + " by " + self.artist + " at " + str(self.holnum) + " on the billboard hot 100."
pass


def get_songs(board_url):
    print("Fetching latest Holiday Hot 100")
    boardpage = requests.get(board_url)
    boardsoup = BeautifulSoup(boardpage.text, "html.parser")
    find_song_details = boardsoup.find_all(class_= "item-details")
    for song_raw in find_song_details:
        song = Song(title = song_raw.find(class_="item-details__title").get_text(), artist = song_raw.find(class_ = "item-details__artist").get_text(), holnum = find_song_details.index(song_raw) + 1)
        songs_list.append(song)
    pass


def get_spotify_data(song_list):
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
    for song in hot_list:
        spot_hot_list.append((song.title, song.artist, song.holnum, spot_list[hot_list.index(song)]))


def create_table():
    conn = sqlite3.connect("spot_hot.sqlite")
    c = conn.cursor()
    c.execute('''CREATE TABLE spothot
                (title text, artist text, holnum integer, spotnum integer)''')


def insert_rows(combined_list):
    conn = sqlite3.connect("spot_hot.sqlite")
    conn.executemany('''INSERT INTO spothot (title, artist, holnum, spotnum) VALUES (?, ?, ?, ?)''', spot_hot_list)
    conn.commit()
    pass


def execute_scatterplot():
    print("Setting up scatterplot...")
    exes = []
    wys = []
    for song in spot_hot_list:
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
    conn = sqlite3.connect("spot_hot.sqlite")
    print("Printing data for top 25...")
    counter = 1
    while counter > 0:
        print(pandas.read_sql_query('''SELECT holnum, title, artist, spotnum FROM spothot WHERE holnum < 26''', conn))
        prompt = input("To see next 25 songs, type next. Any other input will result in quitting the program. ")
        if prompt.lower() == "next":
            print(pandas.read_sql_query('''SELECT holnum, title, artist, spotnum FROM spothot WHERE holnum BETWEEN 26 and 50''', conn))
            prompt2 = input("To see next 25 songs, type next. Any other input will result in quitting the program. ")
            if prompt2.lower() == "next":
                print(pandas.read_sql_query('''SELECT holnum, title, artist, spotnum FROM spothot WHERE holnum BETWEEN 51 and 75''', conn))
                prompt3 = input("To see next 25 songs, type next. Any other input will result in quitting the program.")
                if prompt3.lower() == "next":
                    print(pandas.read_sql_query('''SELECT holnum, title, artist, spotnum FROM spothot WHERE holnum BETWEEN 75 AND 100''', conn))
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


def load_cache():
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    cache_file = open(CACHE_FILENAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


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
    execute_scatterplot()
    display_info()