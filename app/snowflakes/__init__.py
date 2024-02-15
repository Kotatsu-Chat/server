from datetime import datetime
from enum import Enum

import snowflake


class Epoch(Enum):
    ROLLPLAYER = 1_704_067_200_000

    @property
    def __class__(self):
        # For some stupid reason, we need to fake being an Epoch since using an int shits itself and dies since
        # the code checks if the enum's value, which requires it to be an enum [obviously].
        # it also checks if it's a snowflake Epoch, so we need to fake it.
        return snowflake.Epoch

    # noinspection PyTypeChecker
    def __str__(self) -> int:
        # This is a part of the snowflake.Epoch enum. Yes, it *is* set to return an int! Nice observation!
        return self.name


config = snowflake.SnowflakeConfig(
    epoch=Epoch.ROLLPLAYER,  # Jan 1, 2024. the Epoch enum is needed because this library is fucking stupid
    leading_bit=False,
    timestamp_length=42,
    param1_length=9,
    param2_length=1,  # Needed, despite it being "possible to set it to None", it doesn't work if it is!
    sequence_length=12
)

RollplayerChatSnowflake = snowflake.Snowflake(config)


class BitCounter:
    """
    A counter for the SnowflakeFactory class to use - counts from 0 to however many bits you define.
    """

    def __init__(self, bits: int) -> None:
        self._count = -1  # Start at -1 to make first read 0
        self._max = (2 ** bits) - 1  # Calculate max value based on bits

    def read(self) -> int:
        """
        Returns the current count and iterates it. If the count is greater than the limit in bits, it'll return to 0.
        :return: The count.
        """
        self._count += 1  # Increment count
        # Reset count if it exceeds max value
        if self._count > self._max:
            self._count = 0
        return self._count


class ParameterID(Enum):
    MESSAGE = 0
    CHANNEL = 1
    ROLE = 2
    EMOJI = 3
    USER = 4
    CHANNELGROUP = 5  # Like Guilded's Groups. might remove, not sure
    SERVER = 6
    CATEGORY = 7


class _SnowflakeFactory:
    def __init__(self) -> None:
        self._bc_seq = BitCounter(12)
        pass

    def get_snowflake(self, parameter: int) -> str:
        """
        Generates a unique snowflake.

        Use the ParameterID Enum class to get the parameter.
        :param parameter: What "type" the snowflake is.
        :return: a string, being the snowflake
        """
        return RollplayerChatSnowflake.generate_snowflake(param1=parameter, param2=0, sequence=self._bc_seq.read())

    @staticmethod
    def parse_snowflake(input_snowflake: str) -> (datetime, int, int, int):
        return RollplayerChatSnowflake.parse_snowflake(input_snowflake)


SnowflakeFactory = _SnowflakeFactory()
