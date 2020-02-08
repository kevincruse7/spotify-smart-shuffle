import configparser
import spotipy
import pickle
import random


# Represents a song in the playlist.
class Track:
    def __init__(self, tid=0, name='', artist='', genres=[], energy=0.0, valence=0.0):
        self.tid = tid          # ID of track
        self.name = name        # Name of track
        self.artist = artist    # Artist of track
        self.genres = genres    # Genres of track
        self.energy = energy    # Musical energy of track (from 0.0 to 1.0)
        self.valence = valence  # Musical positiveness of track (from 0.0 to 1.0)


# Read in user and group data from settings.conf.
config = configparser.ConfigParser()
config.read('settings.conf')

# User information
username = config['Client']['username']
client_id = config['Client']['id']
client_secret = config['Client']['secret']

# Playlist information
playlist_name = config['Playlist']['name']

# Track group information
group_data = config['Grouped Tracks']
track_group_names = []
for i in range(len(group_data)):
    track_group_names.append(group_data['group' + str(i + 1)].split('\n'))

# Spotify application information
redirect_uri = 'http://localhost'
scope = 'playlist-read-private playlist-modify-private'

# Get user authorization if a token isn't already cached.
token = spotipy.util.prompt_for_user_token(username,
                                           scope,
                                           client_id=client_id,
                                           client_secret=client_secret,
                                           redirect_uri=redirect_uri)

# Print out all saved albums from user
if token:
    # Get user playlist
    sp = spotipy.Spotify(auth=token)
    playlists = sp.current_user_playlists()['items']
    playlist_id = ''
    for playlist in playlists:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            break
    
    # # Get track names and track/artist IDs from playlist
    # name_ids = []
    # offset = 0
    # track_data = sp.playlist_tracks(playlist_id, offset=offset)['items']
    # while len(track_data) > 0:
    #     name_ids += (list(map(lambda track : {'name' : track['track']['name'],
    #                                           'track_id' : track['track']['id'],
    #                                           'artist_id' : track['track']['artists'][0]['id']},
    #                           track_data)))
    #     offset += 100
    #     track_data = sp.playlist_tracks(playlist_id, offset=offset)['items']
    
    # # Convert track IDs to track objects
    # tracks = []
    # for name_id in name_ids:
    #     # Get additional data for track and artist
    #     track_features = sp.audio_features(name_id['track_id'])[0]
    #     artist_data = sp.artist(name_id['artist_id'])

    #     # Consolidate data for track
    #     tid = name_id['track_id']
    #     name = name_id['name']
    #     artist = artist_data['name']
    #     genres = artist_data['genres']
    #     energy = track_features['energy']
    #     valence = track_features['valence']

    #     # Create track object
    #     tracks.append(Track(tid, name, artist, genres, energy, valence))

    # # Save track data locally (temporary for testing)
    # with open('tracks.pkl', 'wb') as output:
    #     for track in tracks:
    #         pickle.dump(track, output, pickle.HIGHEST_PROTOCOL)

    # Read in local track data (temporary for testing)
    tracks = []
    with open('tracks.pkl', 'rb') as input:
        while True:
            try:
                tracks.append(pickle.load(input))
            except EOFError:
                break
    
    # Convert grouped track names to track objects
    track_groups = []
    for group in track_group_names:
        track_group = []
        for name in group:
            result = list(filter(lambda track : track.name == name, tracks))
            if len(result) == 0:
                print('Track not found: ' + name)
            else:
                track_group.append(result[0])
        track_groups.append(track_group)

    # Values used for shuffling playlist
    genre_transitions = {'classical' : ['jazz'],
                         'jazz' : ['classical', 'jazz', 'rock'],
                         'rock' : ['jazz', 'rock']}
    energy_threshold = 0.2
    valence_threshold = 0.2

    # Sort tracks randomly based on genre, artist, energy, and valence
    shuffled_tracks = [tracks.pop(random.randint(0, len(tracks) - 1))]
    for shuffle_index in range(len(tracks)):
        candidates = []
        for track_index in range(len(tracks) - shuffle_index):
            # Determine genre of current song
            for genre in genre_transitions.keys():
                if genre in shuffled_tracks[shuffle_index].genres:
                    track_genre = genre
                    break

            # Determine candidates to follow current song
            if (track_genre in tracks[track_index].genres
                and abs(shuffled_tracks[shuffle_index].energy - tracks[track_index].energy) < energy_threshold
                and abs(shuffled_tracks[shuffle_index].valence - tracks[track_index].valence) < valence_threshold):
                candidates.append(tracks[track_index])

        # Randomly pick next song among candidates
        if len(candidates) > 0:
            selected_track = candidates[random.randint(0, len(candidates) - 1)]
            
            # Determine if the selected track is part of a grouping
            selected_tracks = None
            for group_index in range(len(track_groups)):
                if selected_track in track_groups[group_index]:
                    selected_tracks = track_groups[group_index]
                    break

            # Add selected track or grouping to new shuffled track list
            if selected_tracks != None:
                shuffled_tracks += selected_tracks
                for track in tracks:
                    if track in selected_tracks:
                        tracks.remove(track)
                        shuffle_index += 1
            else:
                shuffled_tracks.append(selected_track)
                tracks.remove(selected_track)
        else:
            break
    
    for track in shuffled_tracks:
        print(track.name)
else:
    print("Can't get token for " + username)