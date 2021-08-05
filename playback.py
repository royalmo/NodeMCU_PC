import pygame
import alsaaudio
from time import sleep, time
from datetime import datetime
from os import listdir
from random import shuffle
from json import loads, dumps

# Setting the volume to 100%
m = alsaaudio.Mixer('Headphone')
m.setvolume(100)

# Starting the player
pygame.init()
pygame.mixer.pre_init(devicename="bcm2835 Headphones, bcm2835 Headphones")
pygame.mixer.init()
player = pygame.mixer.music

# Setup the end track event
player.set_endevent ( pygame.USEREVENT )

class PlayList:
    def __init__(self, song_paths = None, start_time=None, end_time=None, repeats_every=0, song_folder = None, use_import = None):
        self.song_paths = song_paths if song_paths is not None else []
        self.start_time = start_time
        self.end_time = end_time
        self.enabled = False
        self.__playing = False
        self.current_song = 0
        self.repeats_every = repeats_every
        self.song_folder = song_folder

        # Adding songs folder if needed
        if self.song_folder is not None:
            self.update_folder()

        # Importing if needed
        if use_import is not None:
            self.song_paths    = use_import["song_paths"]
            self.start_time    = use_import["start_time"]
            self.end_time      = use_import["end_time"]
            self.enabled       = use_import["enabled"]
            self.current_song  = use_import["current"]
            self.repeats_every = use_import["repeats"]

        # Validating times and lists
        assert (self.start_time < self.end_time) if self.start_time is not None else (self.start_time == self.end_time)
        assert len(self.song_paths) > 0

    def update_folder(self):
        if self.song_folder[-1] ==  "/":
            self.song_folder = self.song_folder[:-1]

        self.song_paths = [self.song_folder + "/" + song for song in listdir(self.song_folder)]

    def shuffle(self):
        shuffle(self.song_paths)

    def is_in_play_time(self):
        if self.start_time is None:
            return True

        current_time = time()
        return current_time > self.start_time and current_time < self.end_time

    def update_times(self):
        if self.repeats_every == 0 or self.start_time is None:
            return

        if self.is_in_play_time():
            return

        current_time = time()

        while self.start_time > current_time:
            self.start_time -= self.repeats_every
            self.end_time -= self.repeats_every

        if self.is_in_play_time():
            return

        while self.start_time < current_time:
            self.start_time += self.repeats_every
            self.end_time += self.repeats_every

    def update(self):
        self.update_times()
        
        # Check if we are inside the time or not.
        if self.is_in_play_time():
            if not self.enabled:
                self.stop()
            elif self.is_playing():
                self.append_song_if_needed()
            else:
                self.start()

        else:
            self.stop()
            
    def start(self):
        self.__playing = True
        self.__load_first()
        player.play()
        self.__queue_next()

    def stop(self):
        self.__playing = False
        player.stop()

    def is_playing(self):
        return self.__playing

    def __load_first(self):
        # The first song is loaded differently
        while True:
            try:
                player.load(self.song_paths[self.current_song])
                break
            except pygame.error:
                self.current_song = ( self.current_song + 1 ) % len( self.song_paths )

    def __queue_next(self):
        # As some songs may be corrupted or not found, we skip them instead of
        # crashing the enitre program.
        while True:
            try:
                self.current_song = ( self.current_song + 1 ) % len( self.song_paths )
                player.queue(self.song_paths[self.current_song])
                break
            except pygame.error:
                pass

    def append_song_if_needed(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:  # A track has ended
                self.__queue_next()

    def skip_song(self):
        pygame.event.post(pygame.USEREVENT)

    def export(self):
        """
        Returns a dict containing all the important information about this instance.
        """
        return {
            "song_paths" : self.song_paths,
            "start_time" : self.start_time,
            "end_time"   : self.end_time,
            "enabled"    : self.enabled,
            "current"    : self.current_song,
            "repeats"    : self.repeats_every
        }

class PlayListHandler:
    def __init__(self, filepath):
        self.filepath = filepath
        self.load_playlists()

        self.newplaylistid = None
        self.main_folder = ""

    def load_playlists(self, filepath = None):
        """
        When the playlists are stored in a json file in ``filepath``, we load them and
        return the resulting dict.
        """
        if filepath is None:
            filepath = self.filepath

        with open(filepath, "r") as f:
            json_data = loads(f.read())

        self.playlists = {pl_id : PlayList(use_import=pl_data) for pl_id, pl_data in json_data.items()}

    def save_playlists(self, filepath = None):
        if filepath is None:
            filepath = self.filepath

        json_data = { pl_id : pl_data.export() for pl_id, pl_data in self.playlists.items()}

        with open(filepath, "w") as f:
            f.write(dumps(json_data, indent=4))

    def get_playlists_ids(self):
        return self.playlists.keys()

    def get_playlists_info(self):
        """
        Returns a list of (ID, pl.enabled, pl.is_playing())
        """
        return [(key, pl.enabled, pl.is_playing()) for key, pl in self.playlists.items()]

    def get_info_of(self, pl_id):
        assert pl_id in self.playlists.keys()
        pl = self.playlists[pl_id]

        formatted_start = datetime.utcfromtimestamp(pl.start_time).strftime('%Y-%m-%d %H:%M:%S')
        duration = round((pl.end_time-pl.start_time)/3600, 2)
        repeat = round(pl.repeats_every/3600, 2)

        return (pl_id, pl.song_folder, formatted_start, duration, repeat)

    def update(self):
        for pl in self.playlists.values():
            pl.update()

    def new_playlist(self, pl_id, pl_folder, pl_start, pl_end, pl_repeat):
        self.playlists[pl_id] = PlayList(song_folder=self.main_folder+pl_folder, start_time=pl_start, end_time=pl_end, repeats_every=pl_repeat)

        self.save_playlists()

    def edit_playlist(self, pl_id, pl_folder, pl_start, pl_end, pl_repeat):
        self.playlists[pl_id].song_folder = self.main_folder+pl_folder
        self.playlists[pl_id].start_time = pl_start
        self.playlists[pl_id].end_time = pl_end
        self.playlists[pl_id].repeats_every = pl_repeat

        self.playlists[pl_id].update_folder()
        self.playlists[pl_id].update()

        self.save_playlists()

    def delete_playlist(self, pl_id):
        self.playlists[pl_id].enabled = False
        self.playlists[pl_id].update()
        del self.playlists[pl_id]

        self.save_playlists()

    def change_status_playlist(self, pl_id, enabled):
        self.playlists[pl_id].enabled = enabled
        self.playlists[pl_id].update()

        self.save_playlists()


if __name__ == "__main__":
    print(listdir("."))