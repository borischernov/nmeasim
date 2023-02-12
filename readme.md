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
from datetime import datetime, timedelta, timezone
from nmeasim.models import GpsReceiver
gps = GpsReceiver(
    date_time=datetime(2020, 1, 1, 12, 34, 56, tzinfo=timezone.utc),
    output=('RMC',)
)
for i in range(3):
    gps.date_time += timedelta(seconds=1)
    gps.get_output()
```

Output:
```
['$GPRMC,123457.000,A,0000.000,N,00000.000,E,0.0,0.0,010120,,,A*6A']
['$GPRMC,123458.000,A,0000.000,N,00000.000,E,0.0,0.0,010120,,,A*65']
['$GPRMC,123459.000,A,0000.000,N,00000.000,E,0.0,0.0,010120,,,A*64']
```

### Simulation - Get Sentences Immediately

```python
from datetime import datetime
from pprint import pprint
from nmeasim.models import TZ_LOCAL
from nmeasim.simulator import Simulator
sim = Simulator()
with sim.lock:
    # Can re-order or drop some
    sim.gps.output = ('GGA', 'GLL', 'GSA', 'GSV', 'RMC', 'VTG', 'ZDA')
    sim.gps.num_sats = 14
    sim.gps.lat = 1
    sim.gps.lon = 3
    sim.gps.altitude = -13
    sim.gps.geoid_sep = -45.3
    sim.gps.mag_var = -1.1
    sim.gps.kph = 60.0
    sim.gps.heading = 90.0
    sim.gps.mag_heading = 90.1
    sim.gps.date_time = datetime.now(TZ_LOCAL)  # PC current time, local time zone
    sim.gps.hdop = 3.1
    sim.gps.vdop = 5.0
    sim.gps.pdop = (sim.gps.hdop ** 2 + sim.gps.vdop ** 2) ** 0.5
    # Precision decimal points for various measurements
    sim.gps.horizontal_dp = 4
    sim.gps.vertical_dp = 1
    sim.gps.speed_dp = 1
    sim.gps.time_dp = 2
    sim.gps.angle_dp = 1
    # Keep straight course for simulator - don't randomly change the heading
    sim.heading_variation = 0
pprint(list(sim.get_output(3)))
```

Output:
```
['$GPGGA,061545.27,0100.0000,N,00300.0000,E,1,14,3.1,-13.0,M,-45.3,M,,*5F',
 '$GPGLL,0100.0000,N,00300.0000,E,061545.27,A,A*6D',
 '$GPGSA,A,3,1,4,7,8,10,13,14,18,21,24,25,26,5.9,3.1,5.0*3A',
 '$GPGSV,4,1,14,01,09,039,31,04,42,278,31,07,11,136,30,08,01,346,34*7B',
 '$GPGSV,4,2,14,10,52,255,35,13,56,061,34,14,12,053,38,18,77,241,38*77',
 '$GPGSV,4,3,14,21,48,056,31,24,09,039,40,25,64,000,36,26,08,131,33*7B',
 '$GPGSV,4,4,14,29,48,213,33,30,33,334,34,,,,,,,,*7B',
 '$GPRMC,061545.27,A,0100.0000,N,00300.0000,E,32.4,90.0,120223,1.1,W,A*2F',
 '$GPVTG,90.0,T,90.1,M,32.4,N,60.0,K,A*21',
 '$GPZDA,061545.27,12,02,2023,13,00*60',
 '$GPGGA,061546.27,0100.0000,N,00300.0090,E,1,14,3.1,-13.0,M,-45.3,M,,*55',
 '$GPGLL,0100.0000,N,00300.0090,E,061546.27,A,A*67',
 '$GPGSA,A,3,1,4,7,8,10,13,14,18,21,24,25,26,5.9,3.1,5.0*3A',
 '$GPGSV,4,1,14,01,08,038,31,04,42,278,30,07,10,136,30,08,01,346,33*7C',
 '$GPGSV,4,2,14,10,52,255,34,13,56,060,34,14,12,052,37,18,76,240,38*79',
 '$GPGSV,4,3,14,21,48,055,30,24,09,039,39,25,63,360,35,26,08,131,32*77',
 '$GPGSV,4,4,14,29,48,213,32,30,33,334,34,,,,,,,,*7A',
 '$GPRMC,061546.27,A,0100.0000,N,00300.0090,E,32.4,90.0,120223,1.1,W,A*25',
 '$GPVTG,90.0,T,90.1,M,32.4,N,60.0,K,A*21',
 '$GPZDA,061546.27,12,02,2023,13,00*63',
 '$GPGGA,061547.27,0100.0000,N,00300.0180,E,1,14,3.1,-13.0,M,-45.3,M,,*54',
 '$GPGLL,0100.0000,N,00300.0180,E,061547.27,A,A*66',
 '$GPGSA,A,3,1,4,7,8,10,13,14,18,21,24,25,26,5.9,3.1,5.0*3A',
 '$GPGSV,4,1,14,01,08,038,30,04,41,277,30,07,10,135,29,08,00,345,33*78',
 '$GPGSV,4,2,14,10,51,254,34,13,55,060,33,14,11,052,37,18,76,240,37*73',
 '$GPGSV,4,3,14,21,47,055,30,24,08,038,39,25,63,359,35,26,07,131,32*7D',
 '$GPGSV,4,4,14,29,47,212,32,30,32,333,33,,,,,,,,*75',
 '$GPRMC,061547.27,A,0100.0000,N,00300.0180,E,32.4,90.0,120223,1.1,W,A*24',
 '$GPVTG,90.0,T,90.1,M,32.4,N,60.0,K,A*21',
 '$GPZDA,061547.27,12,02,2023,13,00*62']
```

### Simulation - Output Sentences Synchronously

```python
import sys
from nmeasim.simulator import Simulator
sim = Simulator()
sim.generate(3, output=sys.stdout)
```

Output:
```
$GPGGA,061808.129,0000.000,N,00000.000,E,1,12,1.0,0.0,M,,M,,*4D
$GPGLL,0000.000,N,00000.000,E,061808.129,A,A*54
$GPGSA,A,3,7,9,11,12,13,18,19,21,24,25,26,28,,1.0,*31
$GPGSV,3,1,12,07,81,128,33,09,86,142,37,11,52,087,34,12,09,020,34*79
$GPGSV,3,2,12,13,37,257,32,18,87,260,37,19,56,313,31,21,26,052,33*72
$GPGSV,3,3,12,24,82,000,35,25,69,269,33,26,17,316,30,28,28,329,39*72
$GPRMC,061808.129,A,0000.000,N,00000.000,E,0.0,0.0,120223,,,A*63
$GPVTG,0.0,T,,M,0.0,N,0.0,K,A*0D
$GPZDA,061808.129,12,02,2023,13,00*5B
$GPGGA,061809.129,0000.000,N,00000.000,E,1,12,1.0,0.0,M,,M,,*4C
$GPGLL,0000.000,N,00000.000,E,061809.129,A,A*55
$GPGSA,A,3,7,9,11,12,13,18,19,21,24,25,26,28,,1.0,*31
$GPGSV,3,1,12,07,82,128,33,09,86,142,38,11,52,087,34,12,10,020,35*7C
$GPGSV,3,2,12,13,38,257,33,18,87,260,38,19,57,313,31,21,27,052,33*73
$GPGSV,3,3,12,24,82,001,35,25,69,269,34,26,17,317,31,28,29,329,39*75
$GPRMC,061809.129,A,0000.000,N,00000.000,E,0.0,21.9,120223,,,A*58
$GPVTG,21.9,T,,M,0.0,N,0.0,K,A*37
$GPZDA,061809.129,12,02,2023,13,00*5A
$GPGGA,061810.129,0000.000,N,00000.000,E,1,12,1.0,0.0,M,,M,,*44
$GPGLL,0000.000,N,00000.000,E,061810.129,A,A*5D
$GPGSA,A,3,7,9,11,12,13,18,19,21,24,25,26,28,,1.0,*31
$GPGSV,3,1,12,07,82,129,34,09,87,143,38,11,52,088,34,12,10,021,35*74
$GPGSV,3,2,12,13,38,258,33,18,88,261,38,19,57,313,32,21,27,053,33*70
$GPGSV,3,3,12,24,83,001,35,25,69,270,34,26,18,317,31,28,29,330,39*7B
$GPRMC,061810.129,A,0000.000,N,00000.000,E,0.0,23.4,120223,,,A*5F
$GPVTG,23.4,T,,M,0.0,N,0.0,K,A*38
$GPZDA,061810.129,12,02,2023,13,00*52
```

### Simulation - 1PPS to Serial Port (Non-Blocking)

```python
from serial import Serial
from time import sleep
from nmeasim.simulator import Simulator
ser = Serial('COM5')
ser.write_timeout = 0 # Do not block simulator on serial writing
sim = Simulator()
sim.serve(output=ser, blocking=False)
sleep(3)
sim.kill()
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
