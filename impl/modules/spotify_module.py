import os, math, time, spotipy
from queue import LifoQueue

class SpotifyModule:
    def __init__(self, config):
        self.invalid = False
        self.calls = 0
        self.queue = LifoQueue()
        self.config = config
        self.sp = None

        if config is not None and 'Spotify' in config:
            client_id = config['Spotify'].get('client_id', '')
            client_secret = config['Spotify'].get('client_secret', '')
            redirect_uri = config['Spotify'].get('redirect_uri', '')

            if client_id and client_secret and redirect_uri:
                try:
                    os.environ["SPOTIPY_CLIENT_ID"] = client_id
                    os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
                    os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri

                    scope = "user-read-currently-playing, user-read-playback-state, user-modify-playback-state"
                    self.auth_manager = spotipy.SpotifyOAuth(scope=scope, open_browser=True)

                    # Ensure token is available (this opens browser only first time)
                    token_info = self.auth_manager.get_cached_token()
                    if not token_info:
                        print("[Spotify] No cached token found. Please visit this URL to authorize:")
                        print(self.auth_manager.get_authorize_url())
                        # After visiting, paste the redirected URL in terminal if asked.
                        token_info = self.auth_manager.get_access_token(as_dict=True)

                    self.sp = spotipy.Spotify(auth_manager=self.auth_manager, requests_timeout=10)
                    self.isPlaying = False
                except Exception as e:
                    print("[Spotify] Auth failed:", e)
                    self.invalid = True
            else:
                print("[Spotify Module] Empty Spotify client id or secret")
                self.invalid = True
        else:
            print("[Spotify Module] Missing config parameters")
            self.invalid = True

    def isDeviceWhitelisted(self):
        if not self.sp:
            return False
        if 'Spotify' in self.config and 'device_whitelist' in self.config['Spotify']:
            try:
                devices = self.sp.devices()
            except Exception as e:
                print("[Spotify] device check failed:", e)
                return False

            device_whitelist = self.config['Spotify']['device_whitelist']
            for device in devices.get('devices', []):
                if device['name'] in device_whitelist and device['is_active']:
                    return True
            return False
        else:
            return True

    def getCurrentPlayback(self):
        self.calls += 1

        if self.invalid or not self.sp:
            return None

        try:
            track = self.sp.current_user_playing_track()
            if not track:
                print("[Spotify] Nothing currently playing")
                return None

            if self.isDeviceWhitelisted():
                if not track.get('item'):
                    artist, title, art_url = None, None, None
                else:
                    artist = track['item']['artists'][0]['name']
                    if len(track['item']['artists']) >= 2:
                        artist += ", " + track['item']['artists'][1]['name']
                    title = track['item']['name']
                    art_url = track['item']['album']['images'][0]['url']

                self.isPlaying = track.get('is_playing', False)

                self.queue.put((
                    artist, title, art_url, self.isPlaying,
                    track.get("progress_ms", 0),
                    track['item']['duration_ms'] if track.get('item') else 0
                ))
        except Exception as e:
            print("[Spotify] Playback fetch failed:", e)
            return None
