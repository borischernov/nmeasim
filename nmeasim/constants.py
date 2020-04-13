from enum import Enum


class NiceEnum(Enum):
    @classmethod
    def nice_names(cls):
        return [cls.__get_nice_name(n) for n in cls.__members__.keys()]

    @staticmethod
    def __get_nice_name(name):
        return name.replace('_', ' ')

    @property
    def nice_name(self):
        return self.__get_nice_name(self.name)

    @classmethod
    def from_nice_name(cls, name):
        return cls[name.replace(' ', '_')]


class FixType(NiceEnum):
    INVALID_FIX = '0'
    SPS_FIX = '1'
    DGPS_FIX = '2'
    PPS_FIX = '3'
    RTK_FIX = '4'
    FLOAT_RTK_FIX = '5'
    DEAD_RECKONING_FIX = '6'
    MANUAL_INPUT_FIX = '7'
    SIMULATED_FIX = '8'

    @property
    def uses_svs(self):
        return self not in (
            FixType.INVALID_FIX,
            FixType.DEAD_RECKONING_FIX,
            FixType.MANUAL_INPUT_FIX,
            FixType.SIMULATED_FIX)


class SolutionMode(NiceEnum):
    """Constants for the NMEA 2.3 specified 'mode'"""
    AUTONOMOUS_SOLUTION = 'A'
    DIFFERENTIAL_SOLUTION = 'D'
    ESTIMATED_SOLUTION = 'E'
    INVALID_SOLUTION = 'N'
    SIMULATOR_SOLUTION = 'S'


class Validity(Enum):
    """Constants for RMC and GLL validity"""
    VALID_FIX = 'A'
    INVALID_FIX = 'V'


class DimensionMode(Enum):
    AUTOMATIC_MODE = 'A'
    MANUAL_MODE = 'M'


class SolutionDimension(Enum):
    SOLUTION_NA = '1'
    SOLUTION_2D = '2'
    SOLUTION_3D = '3'
