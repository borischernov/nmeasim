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
- Custom precision can be specified for all measurements
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

## Building

This project uses a [`PEP 617`](https://peps.python.org/pep-0517/) / [`PEP 621`](https://peps.python.org/pep-0621/) build system, using the `setuptools` backend. A stub `setup.py` exists only to enable editable installs.

The preferred (and tested) frontend is [`build`](https://pypi.org/project/build/).

**Note**: If building with `python -m build --no-isolation`, the build dependencies will not be installed automatically. Instead, you will need to manually install the packages listed under `requires` in the `[build-system]` section of [`pyproject.toml`](pyproject.toml).


## Examples

### Use Model Directly to Set Parameters and Get Sentences

```python
>>> from datetime import datetime, timedelta, timezone
>>> from nmeasim.models import GpsReceiver
>>> gps = GpsReceiver(
...     date_time=datetime(2020, 1, 1, 12, 34, 56, tzinfo=timezone.utc),
...     output=('RMC',)
... )
>>> for i in range(3):
...     gps.date_time += timedelta(seconds=1)
...     gps.get_output()
... 
['$GPRMC,123457.000,A,0000.000,N,00000.000,E,0.0,0.0,010120,,,A*6A']
['$GPRMC,123458.000,A,0000.000,N,00000.000,E,0.0,0.0,010120,,,A*65']
['$GPRMC,123459.000,A,0000.000,N,00000.000,E,0.0,0.0,010120,,,A*64']
```

### Simulation - Get Sentences Immediately

```python
>>> from datetime import datetime
>>> from pprint import pprint
>>> from nmeasim.models import TZ_LOCAL
>>> from nmeasim.simulator import Simulator
>>> sim = Simulator()
>>> with sim.lock:
...     # Can re-order or drop some
...     sim.gps.output = ('GGA', 'GLL', 'GSA', 'GSV', 'RMC', 'VTG', 'ZDA')
...     sim.gps.num_sats = 14
...     sim.gps.lat = 1
...     sim.gps.lon = 3
...     sim.gps.altitude = -13
...     sim.gps.geoid_sep = -45.3
...     sim.gps.mag_var = -1.1
...     sim.gps.kph = 60.0
...     sim.gps.heading = 90.0
...     sim.gps.mag_heading = 90.1
...     sim.gps.date_time = datetime.now(TZ_LOCAL)  # PC current time, local time zone
...     sim.gps.hdop = 3.1
...     sim.gps.vdop = 5.0
...     sim.gps.pdop = (sim.gps.hdop ** 2 + sim.gps.vdop ** 2) ** 0.5
...     # Precision decimal points for various measurements
...     sim.gps.horizontal_dp = 4
...     sim.gps.vertical_dp = 1
...     sim.gps.speed_dp = 1
...     sim.gps.time_dp = 2
...     sim.gps.angle_dp = 1
...     # Keep straight course for simulator - don't randomly change the heading
...     sim.heading_variation = 0
...
>>> pprint(list(sim.get_output(3)))
['$GPGGA,133816.75,0100.0000,N,00300.0000,E,1,14,3.1,-13.0,M,-45.3,M,,*55',
 '$GPGLL,0100.0000,N,00300.0000,E,133816.75,A,A*67',
 '$GPGSA,A,3,1,2,6,8,11,13,15,19,20,23,28,29,5.9,3.1,5.0*38',
 '$GPGSV,0,1,14,01,24,171,32,02,72,298,31,06,08,242,36,08,79,280,36*7C',
 '$GPGSV,1,2,14,11,58,336,34,13,13,140,37,15,90,316,35,19,08,063,30*7B',
 '$GPGSV,2,3,14,20,69,097,36,23,31,103,37,28,02,232,30,29,34,220,31*78',
 '$GPGSV,3,4,14,31,62,108,31,32,20,330,35,,,,,,,,*73',
 '$GPRMC,133816.75,A,0100.0000,N,00300.0000,E,32.4,90.0,170921,1.1,W,A*29',
 '$GPVTG,90.0,T,90.1,M,32.4,N,60.0,K,A*21',
 '$GPZDA,133816.75,17,09,2021,12,00*67',
 '$GPGGA,133817.75,0100.0000,N,00300.0090,E,1,14,3.1,-13.0,M,-45.3,M,,*5D',
 '$GPGLL,0100.0000,N,00300.0090,E,133817.75,A,A*6F',
 '$GPGSA,A,3,1,2,6,8,11,13,15,19,20,23,28,29,5.9,3.1,5.0*38',
 '$GPGSV,0,1,14,01,24,172,33,02,72,298,32,06,09,242,36,08,80,280,37*7B',
 '$GPGSV,1,2,14,11,58,336,34,13,14,141,38,15,90,136,35,19,09,064,31*75',
 '$GPGSV,2,3,14,20,69,097,36,23,31,103,38,28,02,232,31,29,34,220,32*75',
 '$GPGSV,3,4,14,31,62,108,32,32,20,331,35,,,,,,,,*71',
 '$GPRMC,133817.75,A,0100.0000,N,00300.0090,E,32.4,90.0,170921,1.1,W,A*21',
 '$GPVTG,90.0,T,90.1,M,32.4,N,60.0,K,A*21',
 '$GPZDA,133817.75,17,09,2021,12,00*66',
 '$GPGGA,133818.75,0100.0000,N,00300.0180,E,1,14,3.1,-13.0,M,-45.3,M,,*52',
 '$GPGLL,0100.0000,N,00300.0180,E,133818.75,A,A*60',
 '$GPGSA,A,3,1,2,6,8,11,13,15,19,20,23,28,29,5.9,3.1,5.0*38',
 '$GPGSV,0,1,14,01,25,172,33,02,73,299,32,06,09,243,37,08,80,281,37*7B',
 '$GPGSV,1,2,14,11,59,336,34,13,14,141,38,15,90,316,36,19,09,064,31*77',
 '$GPGSV,2,3,14,20,70,098,37,23,32,103,38,28,03,232,31,29,35,221,32*71',
 '$GPGSV,3,4,14,31,63,109,32,32,20,331,36,,,,,,,,*72',
 '$GPRMC,133818.75,A,0100.0000,N,00300.0180,E,32.4,90.0,170921,1.1,W,A*2E',
 '$GPVTG,90.0,T,90.1,M,32.4,N,60.0,K,A*21',
 '$GPZDA,133818.75,17,09,2021,12,00*69']
```

### Simulation - Output Sentences Synchronously

```python
>>> import sys
>>> from nmeasim.simulator import Simulator
>>> sim = Simulator()
>>> sim.generate(3, output=sys.stdout)
$GPGGA,134437.004,0000.000,N,00000.000,E,1,12,1.0,0.0,M,,M,,*42
$GPGLL,0000.000,N,00000.000,E,134437.004,A,A*5B
$GPGSA,A,3,1,4,5,8,9,11,16,21,23,26,30,32,,1.0,*01
$GPGSV,0,1,12,01,25,105,32,04,78,242,31,05,83,185,31,08,21,181,38*7D
$GPGSV,1,2,12,09,89,102,36,11,68,048,32,16,28,229,39,21,90,276,33*73
$GPGSV,2,3,12,23,30,332,33,26,47,120,37,30,50,067,33,32,53,152,31*7F
$GPRMC,134437.004,A,0000.000,N,00000.000,E,0.0,0.0,170921,,,A*60
$GPVTG,0.0,T,,M,0.0,N,0.0,K,A*0D
$GPZDA,134437.004,17,09,2021,12,00*59
$GPGGA,134438.004,0000.000,N,00000.000,E,1,12,1.0,0.0,M,,M,,*4D
$GPGLL,0000.000,N,00000.000,E,134438.004,A,A*54
$GPGSA,A,3,1,4,5,8,9,11,16,21,23,26,30,32,,1.0,*01
$GPGSV,0,1,12,01,24,105,31,04,77,242,31,05,82,185,31,08,20,181,38*70
$GPGSV,1,2,12,09,88,101,36,11,67,047,32,16,28,229,38,21,89,276,33*78
$GPGSV,2,3,12,23,29,332,33,26,46,119,37,30,49,067,33,32,53,151,31*77
$GPRMC,134438.004,A,0000.000,N,00000.000,E,0.0,4.7,170921,,,A*6C
$GPVTG,4.7,T,,M,0.0,N,0.0,K,A*0E
$GPZDA,134438.004,17,09,2021,12,00*56
$GPGGA,134439.004,0000.000,N,00000.000,E,1,12,1.0,0.0,M,,M,,*4C
$GPGLL,0000.000,N,00000.000,E,134439.004,A,A*55
$GPGSA,A,3,1,4,5,8,9,11,16,21,23,26,30,32,,1.0,*01
$GPGSV,0,1,12,01,24,104,31,04,77,241,31,05,82,184,30,08,20,180,37*7C
$GPGSV,1,2,12,09,88,101,35,11,67,047,31,16,28,228,38,21,89,276,32*78
$GPGSV,2,3,12,23,29,332,33,26,46,119,37,30,49,067,32,32,52,151,30*76
$GPRMC,134439.004,A,0000.000,N,00000.000,E,0.0,6.6,170921,,,A*6E
$GPVTG,6.6,T,,M,0.0,N,0.0,K,A*0D
$GPZDA,134439.004,17,09,2021,12,00*57
```

### Simulation - 1PPS to Serial Port (Non-Blocking)

```python
>>> from serial import Serial
>>> from time import sleep
>>> from nmeasim.simulator import Simulator
>>> ser = Serial('COM5')
>>> ser.write_timeout = 0 # Do not block simulator on serial writing
>>> sim = Simulator()
>>> sim.serve(output=ser, blocking=False)
>>> sleep(3)
>>> sim.kill()
```

### Simulation - 1PPS to Serial Port (Blocking)

```python
from serial import Serial
from time import sleep
from threading import Thread
from nmeasim.simulator import Simulator
ser = Serial('COM5')
ser.write_timeout = 0 # Do not block simulator on serial writing
sim = Simulator()
worker = Thread(target=sim.serve, kwargs=dict(output=ser, blocking=True))
worker.start()
sleep(3)
sim.kill()
worker.join()
```

## License

```
Copyright (c) 2021 Wei Li Jiang

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Includes Public Domain icons from the Tango Desktop Project.
```
