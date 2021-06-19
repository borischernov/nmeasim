# nmeasim

A Python 3 GNSS/NMEA receiver simulation.

A partial rewrite of the Python 2 [`gpssim`](https://pypi.org/project/gpssim/) project, originally used to generate test data for NMEA consumers.

## Overview

The core of the package is `nmeasim.simulator`, a GNSS simulation library that emits NMEA sentences. The following are supported:

**Geospatial (GGA, GLL, RMC, VTG, ZDA)** - simulated using a consistent location/velocity model, time using machine time (not NTP, unless the machine happens to be NTP synchronised).

**Satellites (GSA, GSV)** - faked with random azimuth/elevation.

The library supports GP (GPS) and GL (Glonass) sentences. GN (fused GNSS) sentences are not currently supported. Additional GNSS types could be added without too much difficulty by extending `nmeasim.models`.

## GUI

Also included is `nmea.gui`, a Tk GUI that supports serial output to emulate a serial GPS modem. Currently this only supports GP (GPS) sentences.

Features:

- Static / constant velocity / random walk iteration
- Optionally set a target location to route to
- Custom update interval and simulation speed
- Option to simulate independent RTC (time with no fix)
- Custom precision all all measurements
- Custom sentence order and presence
- Simulate fix/no-fix conditions
- Simulate changing satellite visibility

This can be run from source using the console script `nmeasim`.
The GUI is also delivered as a standalone Windows application by the build pipeline - this can be downloaded and executed independently without any Python dependencies.


## Install

```sh
python -m pip install nmeasim
```

See [releases](https://gitlab.com/nmeasim/nmeasim/-/releases) for pre-built Windows GUI binaries.

## License

```
Copyright (c) 2021 Wei Li Jiang

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Includes Public Domain icons from the Tango Desktop Project.
```
