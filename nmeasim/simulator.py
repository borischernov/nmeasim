import datetime
import math
import serial
import sys
import threading
import time
from random import random

from . import models


class Simulator(object):
    '''
    Provides simulated NMEA output based on a models.GnssReceiver instance over serial and/or stdout.
    Supports satellite model perturbation and random walk heading adjustment.
    '''

    def __init__(self, gps=None, glonass=None, static=False, heading_variation=45):
        ''' Initialise the GPS simulator instance with initial configuration.
        '''
        self.__worker = threading.Thread(target=self.__action)
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
        self.comport = serial.Serial()
        self.comport.baudrate = 4800
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

    def __action(self):
        ''' Worker thread action for the GPS simulator - outputs data to the specified serial port at 1PPS.
        '''
        self.__run.set()
        with self.lock:
            if self.comport.port is not None:
                self.comport.open()
        while self.__run.is_set():
            start = time.monotonic()
            if self.__run.is_set():
                with self.lock:
                    output = []
                    for gnss in self.gnss:
                        output += gnss.get_output()
            if self.__run.is_set():
                for sentence in output:
                    if not self.__run.is_set():
                        break
                    print(sentence)
                    if self.comport.port is not None:
                        self.comport.write(f'{sentence}\r\n'.encode())

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

        with self.lock:
            if self.comport.port is not None:
                self.comport.close()

    def serve(self, comport, blocking=True):
        ''' Start serving GPS simulator on the specified COM port (and stdout)
            and optionally blocks until an exception (e.g KeyboardInterrupt).
          Port may be None to send to stdout only.
        '''
        self.kill()
        with self.lock:
            self.comport.port = comport
        self.__worker = threading.Thread(target=self.__action)
        self.__worker.daemon = True
        self.__worker.start()
        if blocking:
            try:
                while True:
                    self.__worker.join(60)
            except:
                self.kill()

    def kill(self):
        ''' Issue the kill command to the GPS simulator thread and wait for it to die.
        '''
        try:
            while self.__worker.is_alive():
                self.__run.clear()
                self.__worker.join(0.1)
        except KeyboardInterrupt:
            pass

    def is_running(self):
        ''' Is the simulator currently running?
        '''
        return self.__run.is_set() or self.__worker.is_alive()

    def generate(self, duration):
        ''' Instantaneous generator for the GPS simulator - outputs data to stdout synchronously.
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
                    print(sentence)
                self.__step(self.step)
                now = self.gps.date_time

    def output_latest(self, comport):
        '''Ouput the latest fix to a specified COM port.
        '''
        with self.lock:
            self.comport.port = comport
            self.comport.open()
            for gnss in self.gnss:
                for sentence in gnss.get_output():
                    self.comport.write(f'{sentence}\r\n'.encode())
            self.comport.close()
