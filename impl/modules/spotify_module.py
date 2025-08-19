import os, math, time, spotipy
from queue import LifoQueue

class SpotifyModule:
    def __init__(self, config):
        self.invalid = False
        self.calls = 0
        self.queue = LifoQueue()
        self.config = config
        
        if config is not None and 'Spotify' in config and 'client_id' in config['Spotify'] \
            and 'client_secret' in config['Spotify'] and 'redirect_uri' in config['Spotify']:
            
            client_id = config['Spotify']['client_id']
            client_secret = config['Spotify']['client_secret']
            redirect_uri = config['Spotify']['redirect_uri']
            if client_id != "" and client_secret != "" and redirect_uri != "":
                try:
                    os.environ["SPOTIPY_CLIENT_ID"] = client_id
                    os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
                    os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri

                    scope = "user-read-currently-playing, user-read-playback-state, user-modify-playback-state"
                    self.auth_manager = spotipy.SpotifyOAuth(scope=scope, open_browser=False)
                    print(self.auth_manager.get_authorize_url())
                    self.sp = spotipy.Spotify(auth_manager=self.auth_manager, requests_timeout=10)
                    self.isPlaying = False
                except Exception as e:
                    print(e)
                    self.invalid = True
            else:
                print("[Spotify Module] Empty Spotify client id or secret")
                self.invalid = True
        else:
            print("[Spotify Module] Missing config parameters")
            self.invalid = True
    
    def isDeviceWhitelisted(self):
        if self.config is not None and 'Spotify' in self.config and 'device_whitelist' in self.config['Spotify']:
            try:
                devices = self.sp.devices()
            except Exception as e:
                print(e)
                return False
            
            device_whitelist = self.config['Spotify']['device_whitelist']
            for device in devices['devices']:
                if device['name'] in device_whitelist and device['is_active']:
                    return True
            return False
        else:
            return True

    def getCurrentPlayback(self):
        self.calls +=1
        print("spotify fetches: " + str(self.calls))

        if self.invalid:
            return
        try:
            track = self.sp.current_user_playing_track()

            if (track is not None and self.isDeviceWhitelisted()):
                if (track['item'] is None):
                    artist = None
                    title = None
                    art_url = None
                else:
                    artist = track['item']['artists'][0]['name']
                    if len(track['item']['artists']) >= 2:
                        artist = artist + ", " + track['item']['artists'][1]['name']
                    title = track['item']['name']
                    art_url = track['item']['album']['images'][0]['url']
                self.isPlaying = track['is_playing']

                self.queue.put((artist, title, art_url, self.isPlaying, track["progress_ms"], track["item"]["duration_ms"]))
        except Exception as e:
            print(e)

