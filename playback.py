import vlc
from time import sleep
from functions import get_path, load_json_file, dump_json_file

class RaspiPlayer(MediaPlayer):
    def __init__(self):
        self.mp = MediaPlayer.__init__(self.random_song())
    def random_song(self):
        return "/home/pi/NodeMCU_PC/audio/001_Ristar_Crazy_Kings.mp3"
def update_song_data():
    pass

def check_for_cmd():
    jin = load_json_file("audio_info.json")
    return jin["request"]

def update_config():
    configs = load_json_file("config.json")
    audio_path = configs["music-folder"]

if __name__ == "__main__":

    update_config()
    
    p = vlc.MediaPlayer("/home/pi/NodeMCU_PC/audio/001_Ristar_Crazy_Kings.mp3")
    print(p.audio_output_set( "default" ))
    p.play()
    sleep(2)
    p.pause()
    sleep(2)
    p.play()
    sleep(2)
    p.stop()
