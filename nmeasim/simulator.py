import datetime
import math
import threading
import time
from random import random
from sys import stdout

from . import models


class Simulator(object):
    '''
    Provides simulated NMEA output based on a models.GnssReceiver instance.
    Supports satellite model perturbation and random walk heading adjustment.
    '''

    def __init__(self, gps=None, glonass=None, static=False, heading_variation=45):
        ''' Initialise the GPS simulator instance with initial configuration.
        '''
        self.__worker = None
        self.__run = threading.Event()
        if gps is None:
            gps = models.GpsReceiver()
        self.gps = gps
        self.glonass = glonass
        self.gnss = [gps]
        if glonass is not None:
            self.gnss.append(glonass)
        self.heading_variation = heading_variation
        self.static = static
        self.target = None
        self.interval = 1.0
        self.step = 1.0
        self.delimiter = '\r\n'
        self.lock = threading.Lock()

    def __step(self, duration=1.0):
        '''
        Iterate a simulation step for the specified duration in seconds,
        moving the GPS instance and updating state.
        Should be called while under lock conditions.
        '''
        if self.static:
            return

        target_heading = None
        rand_heading = (random() - 0.5) * self.heading_variation
        duration_hrs = duration / 3600.0

        for gnss in self.gnss:
            if gnss.date_time is not None and (
                    gnss.num_sats > 0 or gnss.has_rtc):
                gnss.date_time += datetime.timedelta(seconds=duration)

            perturbation = math.sin(gnss.date_time.second * math.pi / 30) / 2
            for satellite in gnss.satellites:
                satellite.snr += perturbation
                satellite.elevation += perturbation
                satellite.azimuth += perturbation

            if gnss.has_fix:
                if self.heading_variation and gnss.heading is not None:
                    if target_heading is None:
                        if self.target:
                            lat, lon = self.target
                            km_to_go, heading = gnss.course(lat, lon)

                            if km_to_go < duration_hrs * gnss.kph:
                                target_heading = heading
                                gnss.kph = km_to_go / duration_hrs
                            else:
                                target_heading = heading + rand_heading
                        else:
                            target_heading = gnss.heading + rand_heading
                    gnss.heading = target_heading
                gnss.move(duration)

    def __write(self, output, sentence, delimiter):
        string = f'{sentence}{delimiter}'
        try:
            output.write(string)
        except TypeError:
            output.write(string.encode())

    def __action(self, output, delimiter):
        ''' Worker thread action for the GPS simulator - outputs data to the specified output at 1PPS.
        '''
        self.__run.set()
        while self.__run.is_set():
            start = time.monotonic()
            if self.__run.is_set():
                with self.lock:
                    sentences = []
                    for gnss in self.gnss:
                        sentences += gnss.get_output()
            if self.__run.is_set():
                for sentence in sentences:
                    if not self.__run.is_set():
                        break
                    self.__write(output, sentence, delimiter)

            if self.__run.is_set():
                time.sleep(0.1)  # Minimum sleep to avoid long lock ups
            while self.__run.is_set() and time.monotonic() - start < self.interval:
                time.sleep(0.1)
            if self.__run.is_set():
                with self.lock:
                    if self.step == self.interval:
                        self.__step(time.monotonic() - start)
                    else:
                        self.__step(self.step)

    def serve(self, output=None, blocking=True, delimiter='\r\n'):
        ''' Start serving GPS simulator to the file-like output (default stdout).
            and optionally blocks until an exception (e.g KeyboardInterrupt).
        '''
        if output is None:
            output = stdout
        self.kill()
        self.__worker = threading.Thread(
            target=self.__action,
            kwargs=dict(output=output, delimiter=delimiter))
        self.__worker.daemon = True
        self.__worker.start()
        if blocking:
            try:
                while self.__worker.is_alive():
                    self.__worker.join(60)
            except:
                self.kill()

    def kill(self):
        ''' Issue the kill command to the GPS simulator thread and wait for it to die.
        '''
        try:
            while self.__worker and self.__worker.is_alive():
                self.__run.clear()
                self.__worker.join(0.1)
        except KeyboardInterrupt:
            pass

    def is_running(self):
        ''' Is the simulator currently running?
        '''
        return self.__run.is_set() or self.__worker and self.__worker.is_alive()

    def get_output(self, duration):
        ''' Instantaneous generator for the GPS simulator.
        Yields one NMEA sentence at a time, without the EOL.
        '''
        with self.lock:
            start = self.gps.date_time
        now = start
        while (now - start).total_seconds() < duration:
            with self.lock:
                output = []
                for gnss in self.gnss:
                    output += gnss.get_output()
                for sentence in output:
                    yield sentence
                self.__step(self.step)
                now = self.gps.date_time

    def generate(self, duration, output=None, delimiter='\r\n'):
        ''' Instantaneous generator for the GPS simulator.
        Synchronously writes data to a file-like output (stdout by default).
        '''
        if output is None:
            output = stdout
        for sentence in self.get_output(duration):
            self.__write(output, sentence, delimiter)

    def output_latest(self, output=None, delimiter='\r\n'):
        '''Ouput the latest fix to a specified file-like output (stdout by default).
        '''
        if output is None:
            output = stdout
        with self.lock:
            for gnss in self.gnss:
                for sentence in gnss.get_output():
                    self.__write(output, sentence, delimiter)