from enum import Enum

from flakemaker import SnowflakeGenerator


class ParameterID(Enum):
    MESSAGE = 0
    CHANNEL = 1
    ROLE = 2
    EMOJI = 3
    USER = 4
    SERVER = 5
    CATEGORY = 6
    INVITE = 7


snowfactory = SnowflakeGenerator()
