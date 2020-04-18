import tkinter as tk
from tkinter.font import Font
import collections
from . import models
from .constants import FixType, SolutionMode
from .simulator import Simulator
import glob
import re
from datetime import datetime
import time
import serial
import sys
import os
from serial.tools import list_ports
from serial import Serial
from importlib.metadata import version
from pathlib import Path


class _NmeaSerialInfo(object):
    @staticmethod
    def ports():
        return [p.device for p in sorted(list_ports.comports())]

    @staticmethod
    def baudrates():
        return Serial.BAUDRATES[Serial.BAUDRATES.index(4800):]


class _Control(object):
    def __init__(
            self,
            master,
            name,
            tk_var_type,
            label):
        self._var = tk_var_type()
        self._label = tk.Label(
            master=master, text=label)

    @property
    def value(self):
        return self._var.get()

    @value.setter
    def value(self, value):
        self._var.set(value)

    def position(self, row):
        self._label.grid(row=row, sticky=tk.E, column=0)
        self._widget.grid(row=row, sticky=tk.W, column=1)

    def disable(self):
        self._widget.configure(state=tk.DISABLED)

    def enable(self):
        self._widget.configure(state=tk.NORMAL)


class _TextBox(_Control):
    def __init__(self, master, name, label):
        super().__init__(
            master=master,
            name=name,
            tk_var_type=tk.StringVar,
            label=label)
        self._widget = tk.Entry(
            master=master,
            textvar=self._var,
            width=60,
            font=Font(size=10)
        )

    @_Control.value.getter
    def value(self):
        raw = self._var.get()
        if len(raw) == 0:
            return None
        else:
            return raw.strip()

    @_Control.value.setter
    def value(self, value):
        self._var.set("" if value is None else str(value))


class _CheckBox(_Control):
    def __init__(self, master, name, label):
        super().__init__(
            master=master,
            name=name,
            tk_var_type=tk.BooleanVar,
            label=label)
        self._widget = tk.Checkbutton(
            master=master,
            text="",
            variable=self._var,
            font=Font(size=10)
        )


class _OptionsList(_Control):
    __background = None

    def __init__(self, master, name, label, options):
        super().__init__(
            master=master,
            name=name,
            tk_var_type=tk.StringVar,
            label=label)
        self._widget = tk.OptionMenu(
            master,
            self._var,
            *tuple(options))

        self._widget.configure(
            font=Font(size=9),
            relief=tk.SUNKEN,
            borderwidth=1,
            activebackground=self._get_background(),
            background=self._get_background(),
        )

    def _get_background(self):
        template = tk.Entry(self._widget.master)
        try:
            return template.cget('background')
        finally:
            template.destroy()


class Interface(object):

    def _add_text_box(self, name, label):
        self._controls[name] = _TextBox(
            self.__frame, name, label)

    def _add_check_box(self, name, label):
        self._controls[name] = _CheckBox(
            self.__frame, name, label)

    def _add_options_list(self, name, label, options):
        self._controls[name] = _OptionsList(
            self.__frame, name, label, options)

    def __init__(self):
        self._sim = Simulator()
        self._sim.gps.kph = 10.0
        self._root = tk.Tk()
        name = "nmeasim"

        try:
            with (Path(sys._MEIPASS) / "version_file").open() as fp:
                version_string = fp.read().strip()
            base_dir = Path(sys._MEIPASS) / name
        except AttributeError:
            base_dir = Path(sys.modules[name].__file__).parent
            version_string = version(name)

        self._root.title('{} {}'.format(name, version_string))
        self._root.iconbitmap(str(base_dir / "icon.ico"))

        # UI collection
        self._controls = collections.OrderedDict()
        self.__frame = tk.LabelFrame(self._root, text="Configuration", padx=5, pady=5)

        self._add_text_box(
            "output", "Formats (ordered)")
        self._add_options_list(
            "comport", "COM port (optional)",
            [""] + _NmeaSerialInfo.ports())
        self._add_options_list(
            "baudrate", "Baud rate",
            _NmeaSerialInfo.baudrates())
        self._add_check_box("static", "Static output")
        self._add_text_box("interval", "Update interval (s)")
        self._add_text_box("step", "Simulation step (s)")
        self._add_text_box(
            "heading_variation", "Simulated heading variation (deg)")
        self._add_options_list(
            "fix", "Fix type",
            self._sim.gps.fix.nice_names())
        self._add_options_list(
            "solution", "FAA solution mode",
            self._sim.gps.solution.nice_names())
        self._add_options_list(
            "num_sats", "Visible satellites", range(self._sim.gps.max_svs + 1))
        self._add_check_box("manual_2d", "Manual 2-D mode")

        self._add_text_box(
            "dgps_station", "DGPS Station ID")
        self._add_text_box(
            "last_dgps", "Time since DGPS update (s)")

        self._add_text_box(
            "date_time", "Initial ISO 8601 date/time/offset")
        self._add_options_list(
            "time_dp", "Time precision (d.p.)", range(4))
        self._add_check_box(
            "has_rtc", "Simulate independent RTC")

        self._add_text_box("lat", "Latitude (deg)")
        self._add_text_box("lon", "Longitude (deg)")
        self._add_text_box("altitude", "Altitude (m)")
        self._add_text_box("geoid_sep", "Geoid separation (m)")
        self._add_options_list(
            "horizontal_dp", "Horizontal precision (d.p.)",
            range(4)
        )
        self._add_options_list(
            "vertical_dp", "Vertical precision (d.p.)",
            range(4)
        )

        self._add_text_box("kph", "Speed (km/hr)")
        self._add_text_box("heading", "Heading (deg True)")
        self._add_text_box("mag_heading", "Magnetic heading (deg True)")
        self._add_text_box("mag_var", "Magnetic variation (deg)")
        self._add_options_list(
            "speed_dp", "Speed precision (d.p.)",
            range(4)
        )
        self._add_options_list(
            "angle_dp", "Angular precision (d.p.)",
            range(4)
        )
        self._add_text_box("hdop", "HDOP")
        self._add_text_box("vdop", "VDOP")
        self._add_text_box("pdop", "PDOP")

        self.__start_stop_button = tk.Button(self._root, text="Start", command=self.start)

        # Pack the controls
        current_row = 0
        for control in self._controls.values():
            control.position(current_row)
            current_row += 1

        self.__frame.pack(padx=5, pady=5, side=tk.TOP)
        self.__start_stop_button.pack(padx=5, pady=5, side=tk.RIGHT)
        self.update()

    def update(self):
        with self._sim.lock:
            self._controls['baudrate'].value = self._sim.comport.baudrate
            self._controls['output'].value = ", ".join(self._sim.gps.output)
            self._controls['static'].value = self._sim.static
            self._controls['interval'].value = self._sim.interval
            self._controls['step'].value = self._sim.step
            self._controls['heading_variation'].value = \
                self._sim.heading_variation

            self._controls['fix'].value = self._sim.gps.fix.nice_name
            self._controls['solution'].value = self._sim.gps.solution.nice_name
            self._controls['num_sats'].value = self._sim.gps.num_sats
            self._controls['manual_2d'].value = self._sim.gps.manual_2d
            self._controls['dgps_station'].value = self._sim.gps.dgps_station
            self._controls['last_dgps'].value = self._sim.gps.last_dgps

            self._controls['date_time'].value = (
                self._sim.gps.date_time.isoformat()
                if self._sim.gps.date_time else None
            )
            self._controls['time_dp'].value = self._sim.gps.time_dp
            self._controls['has_rtc'].value = self._sim.gps.has_rtc

            self._controls['lat'].value = self._sim.gps.lat
            self._controls['lon'].value = self._sim.gps.lon
            self._controls['altitude'].value = self._sim.gps.altitude
            self._controls['geoid_sep'].value = self._sim.gps.geoid_sep
            self._controls['horizontal_dp'].value = self._sim.gps.horizontal_dp
            self._controls['vertical_dp'].value = self._sim.gps.vertical_dp

            self._controls['kph'].value = self._sim.gps.kph
            self._controls['heading'].value = self._sim.gps.heading
            self._controls['mag_heading'].value = self._sim.gps.mag_heading
            self._controls['mag_var'].value = self._sim.gps.mag_var
            self._controls['speed_dp'].value = self._sim.gps.speed_dp
            self._controls['angle_dp'].value = self._sim.gps.angle_dp

            self._controls['hdop'].value = self._sim.gps.hdop
            self._controls['vdop'].value = self._sim.gps.vdop
            self._controls['vdop'].value = self._sim.gps.vdop

    def poll(self):
        if not self._sim.is_running():
            return
        self._root.after(200, self.poll)
        self.update()

    def _convert_model_param(self, name, converter):
        try:
            value = self._controls[name].value
            if value == "":
                value = None
            if value is not None:
                value = converter(value)
            setattr(self._sim.gps, name, value)
        except (TypeError, ValueError):
            pass

    def start(self):
        if self._sim.is_running():
            self._sim.kill()

        self._sim = Simulator()

        # Go through each field and parse them for the simulator
        try:
            self._formats = [
                f.strip() for f in self._controls["output"].value.split(',')]
            self._sim.gps.output = self._formats
        except ValueError:
            pass

        self._sim.static = self._controls["static"].value
        try:
            self._sim.interval = float(self._controls["interval"].value)
        except (TypeError, ValueError):
            pass

        try:
            self._sim.step = float(self._controls["step"].value)
        except (TypeError, ValueError):
            pass

        try:
            value = self._controls["heading_variation"].value
            if value != "":
                value = float(value)
            self._sim.heading_variation = value
        except (TypeError, ValueError):
            pass

        self._sim.gps.fix = self._sim.gps.fix.from_nice_name(
            self._controls["fix"].value)
        self._sim.gps.solution = self._sim.gps.solution.from_nice_name(
            self._controls["solution"].value)
        self._sim.gps.manual_2d = self._controls["manual_2d"].value

        try:
            self._sim.gps.num_sats = int(self._controls["num_sats"].value)
        except (TypeError, ValueError):
            pass

        self._convert_model_param("dgps_station", int)
        self._convert_model_param("last_dgps", int)
        self._convert_model_param("date_time", datetime.fromisoformat)
        self._sim.gps.has_rtc = self._controls["has_rtc"].value
        self._convert_model_param("time_dp", int)

        self._convert_model_param("lat", float)
        self._convert_model_param("lon", float)
        self._convert_model_param("altitude", float)
        self._convert_model_param("geoid_sep", float)
        self._convert_model_param("horizontal_dp", int)
        self._convert_model_param("vertical_dp", int)

        self._convert_model_param("kph", float)
        self._convert_model_param("heading", float)
        self._convert_model_param("mag_heading", float)
        self._convert_model_param("mag_var", float)
        self._convert_model_param("speed_dp", int)
        self._convert_model_param("angle_dp", int)

        self._convert_model_param("hdop", int)
        self._convert_model_param("vdop", int)
        self._convert_model_param("pdop", int)

        self._sim.comport.baudrate = self._controls["baudrate"].value

        self.__start_stop_button.configure(text="Stop", command=self.stop)
        for item in self._controls.keys():
            self._controls[item].disable()
        self.update()

        # Finally start serving
        # (non-blocking as we are in an asynchronous UI thread)
        port = self._controls['comport'].value
        self._sim.serve(comport=None if not port else port, blocking=False)

        # Poll the simulator to update the UI
        self.poll()

    def stop(self):
        if self._sim.is_running():
            self._sim.kill()

        self.update()
        for control in self._controls.values():
            control.enable()
        self.__start_stop_button.configure(text="Start", command=self.start)

    def run(self):
        try:
            self._root.mainloop()
        finally:
            if self._sim.is_running():
                self._sim.kill()


def main():
    gui = Interface()

    # Start the UI!
    try:
        gui.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
