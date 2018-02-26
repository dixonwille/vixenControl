#!/usr/bin/python3
import RPi.GPIO as GPIO
import yaml
import time
import signal
import requests
import sys

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    def exit_gracefully(self, signum, frame):
        self.kill_now = True

class Configuration:
    def __init__(self, filePath):
        with open(filePath, "r") as ymlfile:
            cfgMap = yaml.safe_load(ymlfile)
        self.__dict__.update(**cfgMap)

class Handler:
    def __init__(self, killer, cfg):
        self.cfg = cfg
        self.killer = killer
        self.currState = False
        self.lastState = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cfg.buttonPin, GPIO.IN)
    def start(self):
        while 1:
            self.currState = GPIO.input(self.cfg.buttonPin)
            if self.currState != self.lastState and self.currState:
                self.pressHandler()
            self.lastState = self.currState
            if self.killer.kill_now:
                break
            time.sleep(0.1)
        GPIO.cleanup()
    def pressHandler(self):
        status = self.getStatus()
        if status == None:
            return
        if  len(status) > 0 and 'State' in status[0].keys() and status[0]['State'] == 1:
            self.stop()
        else:
            self.play()
    def play(self):
        try:
            payload = (("Name", self.cfg.seq), ("FileName", self.cfg.seqPath))
            r = requests.post(self.buildAPI("/api/play/playSequence"), timeout=1, data=payload)
            return r.json() 
        except:
            print("Could not play sequence")
            return None
    def stop(self):
        try:
            payload = (("Name", self.cfg.seq), ("FileName", self.cfg.seqPath))
            r = requests.post(self.buildAPI("/api/play/stopSequence"), timeout=1, data=payload)
            return r.json()
        except:
            print("Could not play sequence")
            return None
    def getStatus(self):
        try:
            r = requests.get(self.buildAPI("/api/play/status"), timeout=1)
            return r.json()
        except:
            print("Could not get status")
            return None
    def getSequences(self):
        try:
            r = requests.get(self.buildAPI("/api/play/getSequences"), timeout=1)
            return r.json()
        except:
            print("Could not get sequences")
            return None
    def buildAPI(self, path):
        return self.cfg.host + path

if __name__ == "__main__":
    killer = GracefulKiller()
    cfg = Configuration("/boot/vixenControl.yaml")
    handler = Handler(killer, cfg)
    if len(sys.argv) > 1:
        if sys.argv[1] == "seq":
            print(handler.getSequences())
            sys.exit()
        if sys.argv[1] == "status":
            print(handler.getStatus())
            sys.exit()
    print("Press CTRL+C to stop")
    handler.start()
