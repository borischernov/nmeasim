import collections
from datetime import datetime, timezone
import math
import operator
import random
import sys
import time

from geographiclib.geodesic import Geodesic

from .constants import (
    FixType, SolutionMode, Validity, DimensionMode, SolutionDimension)


TZ_LOCAL = datetime.now().astimezone().tzinfo


class Satellite(object):
    """  class for a GNSS satellite
    """

    def __init__(self, prn, elevation=0, azimuth=0, snr=40):
        self.prn = prn
        self.elevation = elevation
        self.azimuth = azimuth
        self.snr = snr


class GnssReceiver(object):
    """  class for a GNSS receiver
    Takes in a  GNSS parameters and outputs the requested NMEA sentences.
    The  has the capability to project forward 2-D coordinates based on
    a speed and heading over a given time.
    """

    __GSA_SV_LIMIT = 12  # Maximum number of satellites per GSA message
    __GSV_SV_LIMIT = 4  # Maximum number of satellites per GSV message
    __KNOTS_PER_KPH = 1.852

    def __recalculate(self):
        """ Recalculate and fix internal state data for the GNSS instance.
        Should be executed after external modification of parameters
        and prior to doing any calculations.
        """
        self.__visible_prns = []
        for satellite in self.satellites:
            # Fix elevation wrap around (overhead and opposite side of earth)
            if satellite.elevation > 90:
                satellite.elevation = 180 - satellite.elevation
                satellite.azimuth += 180
            elif satellite.elevation < -90:
                satellite.elevation = -180 - satellite.elevation
                satellite.azimuth += 180

            # Fix azimuth wrap around
            satellite.azimuth %= 360

            # Fix SNR going over or under limits
            if satellite.snr < 0:
                satellite.snr = 0
            elif satellite.snr > 99:
                satellite.snr = 99

            if satellite.elevation > 0:
                # If above horizon, treat as visible
                self.__visible_prns.append(satellite.prn)

        # Optional NMEA 2.3 solution 'mode' has priority if present when
        # determining validity
        if self.solution == SolutionMode.INVALID_SOLUTION:
            self.fix = FixType.INVALID_FIX

        # For real fixes correct for number of satellites
        if self.fix.uses_svs:
            # Cannot have a fix if too few satellites
            if self.num_sats < 4:
                self.fix = FixType.INVALID_FIX

        # Force blank fields if there is no fix
        if not self.has_fix:
            self.__validity = Validity.INVALID_FIX
            self.__dimension = SolutionDimension.SOLUTION_NA
        else:
            self.__validity = Validity.VALID_FIX
            self.__dimension = SolutionDimension.SOLUTION_3D

        # Force blanks for 2-D fix
        if self.altitude is None:
            if self.__dimension != SolutionDimension.SOLUTION_NA:
                self.__dimension = SolutionDimension.SOLUTION_2D

        # Convert decimal latitude to NMEA friendly form
        if self.lat is not None:
            self.__lat_sign = "S" if self.lat < 0 else "N"
            self.__lat_degrees = int(abs(self.lat))
            self.__lat_minutes = (abs(self.lat) - self.__lat_degrees) * 60
            # Take care of weird rounding
            if round(self.__lat_minutes, self.horizontal_dp) >= 60:
                self.__lat_degrees += 1
                self.__lat_minutes = 0

        # Convert decimal longitude to NMEA friendly form
        if self.lon is not None:
            self.__lon_sign = "W" if self.lon < 0 else "E"
            self.__lon_degrees = int(abs(self.lon))
            self.__lon_minutes = (abs(self.lon) - self.__lon_degrees) * 60
            # Take care of weird rounding
            if round(self.__lon_minutes, self.horizontal_dp) >= 60:
                self.__lon_degrees += 1
                self.__lon_minutes = 0

        # Convert decimal magnetic variation to NMEA friendly form
        if self.mag_var is not None:
            self.__mag_sign = "W" if self.mag_var < 0 else "E"
            self.__mag_value = abs(self.mag_var)
        else:
            self.__mag_sign = None
            self.__mag_value = None

        # Convert metric speed to imperial form
        self.__knots = self.kph / self.__KNOTS_PER_KPH \
            if self.kph is not None else None

        # Fix heading wrap around
        if self.heading is not None:
            self.heading %= 360

        # Fix magnetic heading wrap around
        if self.mag_heading is not None:
            self.mag_heading %= 360

        # Generate string specifications for various fields
        self.__vertical_spec = f"{{:.{self.vertical_dp}f}}"
        self.__angle_spec = f"{{:.{self.angle_dp}f}}"
        self.__speed_spec = f"{{:.{self.speed_dp}f}}"

        if self.time_dp > 0:
            self.__time_spec = ('%%0%d' % (self.time_dp + 3)
                                ) + ('.%df' % self.time_dp)
        else:
            self.__time_spec = '%02d'

        self.__minute_spec = \
            f"{{:0{self.horizontal_dp + 3}.{self.horizontal_dp}f}}"

        self.__utc = self.date_time.astimezone(timezone.utc) \
            if self.date_time is not None else None

    def __format_sentence(self, data):
        """
        Format an NMEA sentence,
        pre-pending with '$' and post-pending checksum.
        """
        sum = 0
        for ch in data:
            sum ^= ord(ch)
        return f'${data}*{sum:02X}'

    def __nmea_lat_lon(self):
        """ Generate an NMEA lat/lon string (omits final trailing ',').
        """
        parts = []
        if self.lat is not None:
            parts.append(
                f"{{:02d}}{self.__minute_spec}".format(
                    self.__lat_degrees, self.__lat_minutes)
            )
            parts.append(
                self.__lat_sign
            )
        else:
            parts.extend(("", ""))

        if self.lon is not None:
            parts.append(
                f"{{:03d}}{self.__minute_spec}".format(
                    self.__lon_degrees, self.__lon_minutes)
            )
            parts.append(self.__lon_sign)
        else:
            parts.extend(("", ""))

        return ",".join(parts)

    def __nmea_time(self):
        """ Generate an NMEA time string (omits final trailing ',').
        """
        if self.date_time is None:
            return ""

        result = self.__utc.strftime("%H%M%S")
        fractional = self.__utc.strftime("%f")[:self.time_dp]
        if not fractional:
            return result
        return ".".join([result, fractional])

    def __fmt_opt(self, spec, value):
        return f"{spec}".format(
            value) if value is not None else ""

    def __fmt_time(self, spec, value):
        return value.strftime(spec) if value is not None else ""

    def __gga(self):
        """ Generate an NMEA GGA sentence.
        """
        parts = [
            "GGA",
            self.__nmea_time(),
            self.__nmea_lat_lon(),
            self.fix.value,
            f"{self.num_sats:02d}",
            self.__fmt_opt("{:.1f}", self.hdop),
            self.__fmt_opt(self.__vertical_spec, self.altitude),
            "M",
            self.__fmt_opt(self.__vertical_spec, self.geoid_sep),
            "M",
            self.__fmt_opt(self.__time_spec, self.last_dgps),
            self.__fmt_opt("{:04d}", self.dgps_station)
        ]

        return [self.__format_sentence(self._prefix + ",".join(parts))]

    def __rmc(self):
        """ Generate an NMEA RMC sentence.
        """
        parts = [
            "RMC",
            self.__nmea_time(),
            self.__validity.value,
            self.__nmea_lat_lon(),
            self.__fmt_opt(self.__speed_spec, self.__knots),
            self.__fmt_opt(self.__angle_spec, self.heading),
            self.__fmt_time("%d%m%y", self.__utc),
            self.__fmt_opt(self.__angle_spec, self.__mag_value),
            self.__fmt_opt("{}", self.__mag_sign)
        ]

        if self.solution is not None:
            parts.append(self.solution.value)

        return [self.__format_sentence(self._prefix + ",".join(parts))]

    def __gsa(self):
        """ Generate an NMEA GSA sentence.
        """
        parts = [
            "GSA",
            DimensionMode.MANUAL_MODE.value
            if self.manual_2d else DimensionMode.AUTOMATIC_MODE.value,
            self.__dimension.value,
        ]

        entries = min(self.__GSA_SV_LIMIT, self.num_sats)
        parts.extend(
            [f"{p}" for p in self.__visible_prns[:entries]]
        )
        if entries < self.__GSA_SV_LIMIT:
            parts.extend([""] * (self.__GSA_SV_LIMIT - entries))

        parts.extend([
            self.__fmt_opt("{:.1f}", self.pdop),
            self.__fmt_opt("{:.1f}", self.hdop),
            self.__fmt_opt("{:.1f}", self.vdop)
        ])

        return [self.__format_sentence(self._prefix + ",".join(parts))]

    def __gsv(self):
        """ Generate a sequence of NMEA GSV sentences.
        """
        if self.num_sats == 0:
            return []

        # Work out how many GSV sentences are required to show all satellites
        count = int(math.ceil(self.num_sats / self.__GSV_SV_LIMIT))
        messages = []
        prn_i = 0

        # Iterate through each block of satellites
        for i in range(count):
            parts = [
                "GSV",
                f"{len(messages):d}",
                f"{i + 1:d}",
                f"{self.num_sats:02d}"
            ]

            # Iterate through each satellite in the block
            for j in range(self.__GSV_SV_LIMIT):
                if prn_i < self.num_sats:
                    satellite = next((
                        sat for sat in self.satellites if
                        sat.prn == self.__visible_prns[prn_i]
                    ))
                    parts.extend([
                        f"{satellite.prn:02d}",
                        f"{satellite.elevation:02.0f}",
                        f"{satellite.azimuth:03.0f}",
                        f"{satellite.snr:02.0f}"
                    ])
                    prn_i += 1
                else:
                    parts.extend(("", "", "", ""))

            # Generate the GSV sentence for this block
            messages.append(
                self.__format_sentence(self._prefix + ",".join(parts)))

        return messages

    def __vtg(self):
        """ Generate an NMEA VTG sentence.
        """
        parts = [
            "VTG",
            self.__fmt_opt(self.__angle_spec, self.heading),
            "T",
            self.__fmt_opt(self.__angle_spec, self.mag_heading),
            "M",
            self.__fmt_opt(self.__speed_spec, self.__knots),
            "N",
            self.__fmt_opt(self.__speed_spec, self.kph),
            "K"
        ]

        if self.solution is not None:
            parts.append(self.solution.value)

        return [self.__format_sentence(self._prefix + ",".join(parts))]

    def __gll(self):
        """ Generate an NMEA GLL sentence.
        """
        parts = [
            "GLL",
            self.__nmea_lat_lon(),
            self.__nmea_time(),
            self.__validity.value
        ]

        if self.solution is not None:
            parts.append(self.solution.value)

        return [self.__format_sentence(self._prefix + ",".join(parts))]

    def __zda(self):
        """ Generate an NMEA ZDA sentence.
        """
        data = ''

        if self.__utc is None:
            return []

        parts = [
            "ZDA",
            self.__nmea_time(),
            self.__fmt_time("%d", self.__utc),
            self.__fmt_time("%m", self.__utc),
            self.__fmt_time("%Y", self.__utc)
        ]

        offset = self.date_time.utcoffset()
        if offset is not None:
            hh = int(offset.total_seconds() / 3600)
            mm = int(offset.total_seconds() / 60 - hh * 60)
            parts.append(f"{hh:02d}")
            parts.append(f"{mm:02d}")
        else:
            parts.extend(("", ""))

        return [self.__format_sentence(self._prefix + ",".join(parts))]

    def __init__(self,
                 min_sv_number,
                 max_sv_number,
                 total_sv_limit,
                 output=("GGA", "GLL", "GSA", "GSV", "RMC", "VTG", "ZDA"),
                 solution=SolutionMode.AUTONOMOUS_SOLUTION,
                 fix=FixType.SPS_FIX, manual_2d=False,
                 horizontal_dp=3,
                 vertical_dp=1,
                 speed_dp=1,
                 time_dp=3,
                 angle_dp=1,
                 date_time=0,
                 lat=0.0,
                 lon=0.0,
                 altitude=0.0,
                 geoid_sep=None,
                 kph=0.0,
                 heading=0.0,
                 mag_heading=None,
                 mag_var=None,
                 num_sats=12,
                 hdop=1.0,
                 vdop=None,
                 pdop=None,
                 last_dgps=None,
                 dgps_station=None,
                 has_rtc=False):
        """ Initialise the GNSS instance with initial configuration.
        """
        # Populate the sentence generation table

        self._prefix = 'GN'
        self.__min_sv_number = min_sv_number  # Minimum satellite prn
        self.__max_sv_number = max_sv_number  # Maximum satellite prn
        self.__total_sv_limit = total_sv_limit  # Maximum possible satellite constellation size

        self.__gen_nmea = {}
        self.__gen_nmea['GGA'] = self.__gga
        self.__gen_nmea['GSA'] = self.__gsa
        self.__gen_nmea['GSV'] = self.__gsv
        self.__gen_nmea['RMC'] = self.__rmc
        self.__gen_nmea['VTG'] = self.__vtg
        self.__gen_nmea['GLL'] = self.__gll
        self.__gen_nmea['ZDA'] = self.__zda

        # Record parameters
        self.solution = solution
        self.fix = fix
        self.manual_2d = manual_2d
        if (date_time == 0):
            self.date_time = datetime.now(TZ_LOCAL)
        else:
            self.date_time = date_time
        self.lat = lat
        self.lon = lon
        self.horizontal_dp = horizontal_dp
        self.vertical_dp = vertical_dp
        self.speed_dp = speed_dp
        self.angle_dp = angle_dp
        self.time_dp = time_dp
        self.altitude = altitude
        self.geoid_sep = geoid_sep
        self.kph = kph
        self.heading = heading
        self.mag_heading = mag_heading
        self.mag_var = mag_var
        self.hdop = hdop
        self.vdop = vdop
        self.pdop = pdop
        self.last_dgps = last_dgps
        self.dgps_station = dgps_station
        self.output = output
        self.has_rtc = has_rtc

        # Create all dummy satellites with random conditions
        self.satellites = []
        for prn in range(self.__min_sv_number, self.__max_sv_number + 1):
            self.satellites.append(Satellite(
                prn, azimuth=random.random() * 360, snr=30 + random.random() * 10))

        # Smart setter will configure satellites as appropriate
        self.num_sats = num_sats

        self.__recalculate()

    @property
    def max_svs(self):
        return self.__total_sv_limit

    @property
    def lat(self):
        return self._lat

    @lat.setter
    def lat(self, new_lat):
        self._lat = new_lat

    @property
    def lon(self):
        return self._lon

    @lon.setter
    def lon(self, new_lon):
        self._lon = new_lon

    @property
    def altitude(self):
        return self._altitude

    @altitude.setter
    def altitude(self, new_altitude):
        self._altitude = new_altitude

    @property
    def geoid_sep(self):
        return self._geoid_sep

    @geoid_sep.setter
    def geoid_sep(self, new_geoid_sep):
        self._geoid_sep = new_geoid_sep

    @property
    def hdop(self):
        return self._hdop

    @hdop.setter
    def hdop(self, new_hdop):
        self._hdop = new_hdop

    @property
    def vdop(self):
        return self._vdop

    @vdop.setter
    def vdop(self, new_vdop):
        self._vdop = new_vdop

    @property
    def pdop(self):
        return self._pdop

    @pdop.setter
    def pdop(self, new_pdop):
        self._pdop = new_pdop

    @property
    def kph(self):
        return self._kph

    @kph.setter
    def kph(self, new_kph):
        self._kph = new_kph

    @property
    def heading(self):
        return self._heading

    @heading.setter
    def heading(self, new_heading):
        self._heading = new_heading

    @property
    def mag_heading(self):
        return self._mag_heading

    @mag_heading.setter
    def mag_heading(self, new_mag_heading):
        self._mag_heading = new_mag_heading

    @property
    def mag_var(self):
        return self._mag_var

    @mag_var.setter
    def mag_var(self, new_mag_var):
        self._mag_var = new_mag_var

    @property
    def dgps_station(self):
        return self._dgps_station

    @dgps_station.setter
    def dgps_station(self, new_dgps_station):
        self._dgps_station = new_dgps_station

    @property
    def last_dgps(self):
        return self._last_dgps

    @last_dgps.setter
    def last_dgps(self, new_last_dgps):
        self._last_dgps = new_last_dgps

    @property
    def has_rtc(self):
        return self._has_rtc

    @has_rtc.setter
    def has_rtc(self, new_has_rtc):
        self._has_rtc = new_has_rtc

    @property
    def date_time(self):
        return self._date_time

    @date_time.setter
    def date_time(self, new_date_time):
        self._date_time = new_date_time

    @property
    def num_sats(self):
        return len(self.__visible_prns)

    @num_sats.setter
    def num_sats(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid SV count {value}")

        if value < 0 or value > self.__total_sv_limit:
            raise ValueError(f"Invalid SV count {value}")

        # Randomly make the requested number visible, make the rest invisible
        # (negative elevation)
        random.shuffle(self.satellites)
        for i in range(value):
            self.satellites[i].elevation = random.random() * 90
        for i in range(value, len(self.satellites)):
            self.satellites[i].elevation = -90
        self.satellites.sort(key=operator.attrgetter("prn", ))
        self.__recalculate()

    @property
    def output(self):
        return self.__output

    @output.setter
    def output(self, value):
        for item in value:
            if item not in self.__gen_nmea.keys():
                raise ValueError(f"{item} is not a valid NMEA sentence")
        self.__output = value

    @property
    def manual_2d(self):
        return self._manual_2d

    @manual_2d.setter
    def manual_2d(self, value):
        self._manual_2d = value

    @property
    def fix(self):
        return self.__fix

    @fix.setter
    def fix(self, value):
        assert isinstance(value, FixType)
        self.__fix = value

    @property
    def has_fix(self):
        return self.fix != FixType.INVALID_FIX

    @property
    def solution(self):
        if not self.has_fix:
            return SolutionMode.INVALID_SOLUTION
        return self.__solution

    @solution.setter
    def solution(self, value):
        if not value:
            self.__solution = None
        assert isinstance(value, SolutionMode)
        self.__solution = value

    @property
    def horizontal_dp(self):
        return self._horizontal_dp

    @horizontal_dp.setter
    def horizontal_dp(self, value):
        self._horizontal_dp = value

    @property
    def vertical_dp(self):
        return self._vertical_dp

    @vertical_dp.setter
    def vertical_dp(self, value):
        self._vertical_dp = value

    @property
    def speed_dp(self):
        return self._speed_dp

    @speed_dp.setter
    def speed_dp(self, value):
        self._speed_dp = value

    @property
    def angle_dp(self):
        return self._angle_dp

    @angle_dp.setter
    def angle_dp(self, value):
        self._angle_dp = value

    def move(self, duration=1.0):
        """
        'Move' the GNSS instance for the specified duration in seconds
        based on current heading and velocity.
        """
        self.__recalculate()
        if any([x is None for x in (self.lat, self.lon, self.heading, self.kph)]):
            return
        if self.kph > sys.float_info.epsilon:
            speed_ms = self.kph * 1000.0 / 3600.0
            d = speed_ms * duration
            out = Geodesic.WGS84.Direct(self.lat, self.lon, self.heading, d)
            self.lat = out["lat2"]
            self.lon = out["lon2"]
            self.__recalculate()

    def distance(self, other_lat, other_lon):
        """
        Returns the current distance (in km) between the GNSS instance
        and an arbitrary lat/lon coordinate.
        """
        out = Geodesic.WGS84.Inverse(self.lat, self.lon, other_lat, other_lon)
        return out["s12"] / 1000.0

    def get_output(self):
        """
        Returns a list of NMEA sentences (not new line terminated) that
        the GNSS instance was configured to output.
        """
        self.__recalculate()
        outputs = []
        for format in self.output:
            outputs += self.__gen_nmea[format]()
        return outputs

    def supported_output(self):
        """
        Returns a tuple of supported NMEA sentences that
        the GNSS class is capable of producing.
        """
        return self.__gen_nmea.keys()


class GpsReceiver(GnssReceiver):

    def __init__(self, *args, **kwargs):
        super(GpsReceiver, self).__init__(
            min_sv_number=1,
            max_sv_number=32,
            total_sv_limit=32,
            *args,
            **kwargs)
        self._prefix = "GP"


class GlonassReceiver(GnssReceiver):

    def __init__(self, *args, **kwargs):
        super(GlonassReceiver, self).__init__(
            min_sv_number=65,
            max_sv_number=96,
            total_sv_limit=24,
            *args,
            **kwargs)
        self._prefix = "GL"
