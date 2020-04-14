import tkinter
from tkinter import font
import collections
from . import models
from .constants import FixType, SolutionMode
from .simulator import Simulator
import glob
import re
import datetime
import time
import serial
import sys
import os
from serial.tools import list_ports
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

# Scan available serial ports
ports = [p.device for p in sorted(list_ports.comports())]

root = tkinter.Tk()

name = "nmeasim"

try:
    with (Path(sys._MEIPASS) / "version_file").open() as fp:
        version = fp.read().strip()
    base_dir = Path(sys._MEIPASS) / name
except AttributeError:
    base_dir = Path(sys.modules[name].__file__).parent
    version = version(name)

root.title('{} {}'.format(name, version))
root.iconbitmap(str(base_dir / "icon.ico"))

textwidth = 60  # text field width
customFont = font.Font(size=10)
smallerFont = font.Font(size=9)

# UI collection
vars = collections.OrderedDict()
labels = collections.OrderedDict()
controls = collections.OrderedDict()
formats = collections.OrderedDict()

# Create default format strings based on library outputs
defaultformatstring = ''
formats = sorted(models.GpsReceiver().supported_output())
for format in formats:
    defaultformatstring += format
    if format != formats[-1]:
        defaultformatstring += ', '

frame = tkinter.LabelFrame(text='Configuration', padx=5, pady=5)

# Instantiate configuration variables and their respective label/edit fields.
vars['output'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Formats (ordered):')
vars[next(reversed(vars.keys()))].set(defaultformatstring)
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

bgcolor = controls[next(reversed(vars.keys()))].cget('background')

vars['comport'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='COM port (optional):')
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(ports))

vars['baudrate'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Baud rate:')
vars[next(reversed(vars.keys()))].set(4800)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame, vars[next(reversed(vars.keys()))],
                                               *tuple(serial.Serial.BAUDRATES[serial.Serial.BAUDRATES.index(4800):]))

vars['static'] = tkinter.BooleanVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Static output:')
vars[next(reversed(vars.keys()))].set(False)
controls[next(reversed(vars.keys()))] = tkinter.Checkbutton(frame,
                                                text='', variable=vars[next(reversed(vars.keys()))])

vars['static'] = tkinter.BooleanVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Static output:')
vars[next(reversed(vars.keys()))].set(False)
controls[next(reversed(vars.keys()))] = tkinter.Checkbutton(frame,
                                                text='', variable=vars[next(reversed(vars.keys()))])

vars['interval'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Update Interval (s):')
vars[next(reversed(vars.keys()))].set('1.0')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['step'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Simulation Step (s):')
vars[next(reversed(vars.keys()))].set('1.0')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['heading_variation'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Simulated heading variation (deg):')
vars[next(reversed(vars.keys()))].set('')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['fix'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Fix type:')
vars[next(reversed(vars.keys()))].set(FixType.SPS_FIX.nice_name)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(FixType.nice_names()))

vars['solution'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='FAA solution mode:')
vars[next(reversed(vars.keys()))].set(SolutionMode.AUTONOMOUS_SOLUTION.nice_name)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(SolutionMode.nice_names()))

vars['num_sats'] = tkinter.IntVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Visible satellites:')
vars[next(reversed(vars.keys()))].set(15)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(range(33)))

vars['manual_2d'] = tkinter.BooleanVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Manual 2-D mode:')
vars[next(reversed(vars.keys()))].set(False)
controls[next(reversed(vars.keys()))] = tkinter.Checkbutton(frame,
                                                text='', variable=vars[next(reversed(vars.keys()))])

vars['dgps_station'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='DGPS Station ID:')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['last_dgps'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Time since DGPS update (s):')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['date_time'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Initial ISO 8601 date/time/offset:')
vars[next(reversed(vars.keys()))].set(datetime.datetime.now(models.TimeZone(time.timezone)).isoformat())
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['time_dp'] = tkinter.IntVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Time precision (d.p.):')
vars[next(reversed(vars.keys()))].set('3')
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(range(4)))

vars['lat'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Latitude (deg):')
vars[next(reversed(vars.keys()))].set('-45.352354')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['lon'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Longitude (deg):')
vars[next(reversed(vars.keys()))].set('-134.687995')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['altitude'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Altitude (m):')
vars[next(reversed(vars.keys()))].set('-11.442')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['geoid_sep'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Geoid separation (m):')
vars[next(reversed(vars.keys()))].set('-42.55')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['horizontal_dp'] = tkinter.IntVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Horizontal precision (d.p.):')
vars[next(reversed(vars.keys()))].set(3)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(range(1, 6)))

vars['vertical_dp'] = tkinter.IntVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Vertical precision (d.p.):')
vars[next(reversed(vars.keys()))].set(1)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(range(4)))

vars['kph'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Speed (km/hr):')
vars[next(reversed(vars.keys()))].set('45.61')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['heading'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Heading (deg True):')
vars[next(reversed(vars.keys()))].set('123.56')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['mag_heading'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Magnetic heading (deg True):')
vars[next(reversed(vars.keys()))].set('124.67')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['mag_var'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Magnetic Variation (deg):')
vars[next(reversed(vars.keys()))].set('-12.33')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['speed_dp'] = tkinter.IntVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='Speed precision (d.p.):')
vars[next(reversed(vars.keys()))].set(1)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(range(4)))

vars['angle_dp'] = tkinter.IntVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame,
                                        text='Angular precision (d.p.):')
vars[next(reversed(vars.keys()))].set(1)
controls[next(reversed(vars.keys()))] = tkinter.OptionMenu(frame,
                                               vars[next(reversed(vars.keys()))], *tuple(range(4)))

vars['hdop'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='HDOP:')
vars[next(reversed(vars.keys()))].set('3.0')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['vdop'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='VDOP:')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

vars['pdop'] = tkinter.StringVar()
labels[next(reversed(vars.keys()))] = tkinter.Label(frame, text='PDOP:')
controls[next(reversed(vars.keys()))] = tkinter.Entry(frame, textvar=vars[next(reversed(vars.keys()))])

# Pack the controls
current_row = 0
for item in controls.keys():
    labels[item].config(font=customFont)
    labels[item].grid(row=current_row, sticky=tkinter.E, column=0)

    if isinstance(controls[item], tkinter.Entry):
        controls[item].config(width=textwidth, font=customFont)
        controls[item].grid(
            row=current_row, sticky=tkinter.E + tkinter.W, column=1)
    elif isinstance(controls[item], tkinter.OptionMenu):
        controls[item].config(font=smallerFont, relief=tkinter.SUNKEN,
                              borderwidth=1, activebackground=bgcolor, background=bgcolor)
        controls[item].grid(row=current_row, sticky=tkinter.W, column=1)
    else:
        controls[item].grid(row=current_row, sticky=tkinter.W, column=1)
    current_row += 1

# Function that gets called from the UI to start the simulator
sim = Simulator()


def update():
    with sim.lock:
        formatstring = ''
        for format in sim.gps.output:
            formatstring += format
            if format != sim.gps.output[-1]:
                formatstring += ', '

        vars['output'].set(formatstring)
        vars['static'].set(sim.static)
        vars['interval'].set(sim.interval)
        vars['step'].set(sim.step)

        if sim.heading_variation == None:
            vars['heading_variation'].set('')
        else:
            vars['heading_variation'].set(str(sim.heading_variation))

        vars['fix'].set(sim.gps.fix.nice_name)
        vars['solution'].set(sim.gps.solution.nice_name)
        vars['num_sats'].set(sim.gps.num_sats)
        vars['manual_2d'].set(sim.gps.manual_2d)

        if sim.gps.dgps_station == None:
            vars['dgps_station'].set('')
        else:
            vars['dgps_station'].set(str(sim.gps.dgps_station))

        if sim.gps.last_dgps == None:
            vars['last_dgps'].set('')
        else:
            vars['last_dgps'].set(str(sim.gps.last_dgps))

        if sim.gps.date_time == None:
            vars['date_time'].set('')
        else:
            vars['date_time'].set(str(sim.gps.date_time.isoformat()))

        vars['time_dp'].set(sim.gps.time_dp)

        if sim.gps._lat == None:
            vars['lat'].set('')
        else:
            vars['lat'].set(str(sim.gps.lat))

        if sim.gps.lon == None:
            vars['lon'].set('')
        else:
            vars['lon'].set(str(sim.gps.lon))

        if sim.gps.altitude == None:
            vars['altitude'].set('')
        else:
            vars['altitude'].set(str(sim.gps.altitude))

        if sim.gps.geoid_sep == None:
            vars['geoid_sep'].set('')
        else:
            vars['geoid_sep'].set(str(sim.gps.geoid_sep))

        vars['horizontal_dp'].set(sim.gps.horizontal_dp)
        vars['vertical_dp'].set(sim.gps.vertical_dp)

        if sim.gps.kph == None:
            vars['kph'].set('')
        else:
            vars['kph'].set(str(sim.gps.kph))

        if sim.gps.heading == None:
            vars['heading'].set('')
        else:
            vars['heading'].set(str(sim.gps.heading))

        if sim.gps.mag_heading == None:
            vars['mag_heading'].set('')
        else:
            vars['mag_heading'].set(str(sim.gps.mag_heading))

        if sim.gps.mag_var == None:
            vars['mag_var'].set('')
        else:
            vars['mag_var'].set(str(sim.gps.mag_var))

        vars['speed_dp'].set(sim.gps.speed_dp)
        vars['angle_dp'].set(sim.gps.angle_dp)

        if sim.gps.hdop == None:
            vars['hdop'].set('')
        else:
            vars['hdop'].set(str(sim.gps.hdop))

        if sim.gps.vdop == None:
            vars['vdop'].set('')
        else:
            vars['vdop'].set(str(sim.gps.vdop))

        if sim.gps.vdop == None:
            vars['vdop'].set('')
        else:
            vars['pdop'].set(str(sim.gps.pdop))


def poll():
    if sim.is_running():
        root.after(200, poll)
        update()


def start():
    global sim

    if sim.is_running():
        sim.kill()

    sim = Simulator()

    # Change configuration under lock in case its already running from last
    # time
    with sim.lock:

        # Go through each field and parse them for the simulator
        # If anything invalid pops up revert to a safe value (e.g. None)
        try:
            formats = [x.strip() for x in vars['output'].get().split(',')]
            sim.gps.output = formats
        except:
            raise
            vars['output'].set(defaultformatstring)
            formats = [x.strip() for x in vars['output'].get().split(',')]
            sim.gps.output = formats

        sim.static = vars['static'].get()
        try:
            sim.interval = float(vars['interval'].get())
        except:
            sim.interval = 1.0
            vars['interval'].set('1.0')
        try:
            sim.step = float(vars['step'].get())
        except:
            sim.step = 1.0
            vars['step'].set('1.0')

        try:
            sim.heading_variation = float(vars['heading_variation'].get())
        except:
            sim.heading_variation = None
            vars['heading_variation'].set('')

        sim.gps.fix = FixType.from_nice_name(vars['fix'].get())
        sim.gps.solution = SolutionMode.from_nice_name(vars['solution'].get())
        sim.gps.manual_2d = vars['manual_2d'].get()
        sim.gps.num_sats = vars['num_sats'].get()

        try:
            sim.gps.dgps_station = int(vars['dgps_station'].get())
        except:
            sim.gps.dgps_station = None
            vars['dgps_station'].set('')

        try:
            sim.gps.last_dgps = float(vars['last_dgps'].get())
        except:
            sim.gps.last_dgps = None
            vars['last_dgps'].set('')

        dt = vars['date_time'].get()
        if dt == '':
            sim.gps.date_time = None
        else:
            try:
                tz = dt[-6:].split(':')
                dt = dt[:-6]
                utcoffset = int(tz[0]) * 3600 + int(tz[1]) * 60

                sim.gps.date_time = datetime.datetime.strptime(
                    dt, '%Y-%m-%dT%H:%M:%S.%f')
                sim.gps.date_time = sim.gps.date_time.replace(
                    tzinfo=models.TimeZone(utcoffset))
            except:
                sim.gps.date_time = datetime.datetime.now(
                    models.TimeZone(time.timezone))
                vars['date_time'].set(sim.gps.date_time.isoformat())

        sim.gps.time_dp = vars['time_dp'].get()

        try:
            sim.gps._lat = float(vars['lat'].get())
        except:
            sim.gps._lat = None
            vars['lat'].set('')

        try:
            sim.gps.lon = float(vars['lon'].get())
        except:
            sim.gps.lon = None
            vars['lon'].set('')

        try:
            sim.gps.altitude = float(vars['altitude'].get())
        except:
            sim.gps.altitude = None
            vars['altitude'].set('')

        try:
            sim.gps.geoid_sep = float(vars['geoid_sep'].get())
        except:
            sim.gps.geoid_sep = None
            vars['geoid_sep'].set('')

        sim.gps.horizontal_dp = vars['horizontal_dp'].get()

        sim.gps.vertical_dp = vars['vertical_dp'].get()

        try:
            sim.gps.kph = float(vars['kph'].get())
        except:
            sim.gps.kph = None
            vars['kph'].set('')

        try:
            sim.gps.heading = float(vars['heading'].get())
        except:
            sim.gps.heading = None
            vars['heading'].set('')

        try:
            sim.gps.mag_heading = float(vars['mag_heading'].get())
        except:
            sim.gps.mag_heading = None
            vars['mag_heading'].set('')

        try:
            sim.gps.mag_var = float(vars['mag_var'].get())
        except:
            sim.gps.mag_var = None
            vars['mag_var'].set('')

        sim.gps.speed_dp = vars['speed_dp'].get()

        sim.gps.angle_dp = vars['angle_dp'].get()

        try:
            sim.gps.hdop = float(vars['hdop'].get())
        except:
            sim.gps.hdop = None
            vars['hdop'].set('')

        try:
            sim.gps.vdop = float(vars['vdop'].get())
        except:
            sim.gps.vdop = None
            vars['vdop'].set('')

        try:
            sim.gps.pdop = float(vars['pdop'].get())
        except:
            sim.gps.pdop = None
            vars['pdop'].set('')

        sim.comport.baudrate = vars['baudrate'].get()

    # Finally start serving (non-blocking as we are in an asynchronous UI
    # thread)
    port = vars['comport'].get()
    if port == '':
        port = None

    startstopbutton.config(command=stop, text='Stop')
    for item in controls.keys():
        controls[item].config(state=tkinter.DISABLED)
    sim.serve(port, blocking=False)
    poll()


def stop():
    if sim.is_running():
        sim.kill()

    startstopbutton.config(command=start, text='Start')

    update()

    for item in controls.keys():
        controls[item].config(state=tkinter.NORMAL)

startstopbutton = tkinter.Button(root, text='Start', command=start)

def main():
    frame.pack(padx=5, pady=5, side=tkinter.TOP)
    startstopbutton.pack(padx=5, pady=5, side=tkinter.RIGHT)

    # Start the UI!
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        sim.kill()

if __name__ == "__main__":
    main()
