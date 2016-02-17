# -*- coding: utf-8 -*-
# @Author: Catofes
# @Date:   2015-08-15


'''
Class to cache songs into local storage.
'''

from singleton import Singleton
import threading
import subprocess
from const import Constant
from config import Config
import os
import logger
import signal

log = logger.getLogger(__name__)

SYS_SHELL = "/bin/bash"


class Cache(Singleton):
    def __init__(self):
        if hasattr(self, '_init'):
            return
        self._init = True
        self.const = Constant()
        self.config = Config()
        self.download_lock = threading.Lock()
        self.check_lock = threading.Lock()
        self.downloading = []
        self.aria2c = None
        self.stop = False
        self.enable = self.config.get_item("cache")
        self.mpg123_parameters = self.config.get_item("mpg123_parameters")
        self.aria2c_parameters = self.config.get_item("aria2c_parameters")
        self.user_proxy = self.mpg123_parameters[1]


    def start_download(self):
        check = self.download_lock.acquire(False)
        if not check:
            return False
        while True:
            if self.stop:
                break
            if not self.enable:
                break
            log.debug("HEY, download enabled!")
            self.check_lock.acquire()
            if len(self.downloading) <= 0:
                self.check_lock.release()
                break
            data = self.downloading.pop()
            self.check_lock.release()
            song_id = data[0]
            song_name = data[1]
            artist = data[2]
            url = data[3]
            onExit = data[4]
            output_path = Constant.download_dir
            output_file = str(artist) + " - " + str(song_name) + ".mp3"
            # log.debug("hey, output path = "+ output_path)
            # log.debug("hey, output file = "+ output_file)
            try:
                # para = ['aria2c', '--auto-file-renaming=false', '--allow-overwrite=true', '-d', output_path, '-o',
                #         output_file, url]
                # para[1:1] = self.aria2c_parameters

                para = 'aria2c '+ '--auto-file-renaming=false '+ '--allow-overwrite=true '+ '--http-proxy="' + self.user_proxy + '" ' + '-d '+ output_path + ' -o "' + output_file + '" ' + url
                log.debug("final para = " + str(para))

                self.aria2c = subprocess.Popen(para,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    executable = SYS_SHELL, shell = True)

                self.aria2c.wait()
            except Exception:
                log.debug(str(song_id) + " Cache Error")
            if self.aria2c.returncode == 0:
                log.debug(str(song_name) + " Cache OK")
                onExit(song_id, output_path + "/" + output_file)
        self.download_lock.release()


    def add(self, song_id, song_name, artist, url, onExit):
        self.check_lock.acquire()
        log.debug("HEY, I am about to download song: " + song_name)
        self.downloading.append([song_id, song_name, artist, url, onExit])
        self.check_lock.release()

    def quit(self):
        self.stop = True
        try:
            os.kill(self.aria2c.pid, signal.SIGKILL)
        except:
            pass

