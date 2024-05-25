import re
import time
import exrex
import hashlib
import datetime

# Global and static variables, constants
time_format_map = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
    "M": 60 * 60 * 24 * 30,
    "y": 60 * 60 * 24 * 365
}


# ==-----------------------------------------------------------------------------== #
# Cryptography and security                                                         #
# ==-----------------------------------------------------------------------------== #
def md5(string: str) -> str:
    """Hashes string using md5 algorithm."""

    return hashlib.md5(string.encode()).hexdigest()


def sha1(string: str) -> str:
    """Hashes string using sha1 algorithm."""

    return hashlib.sha1(string.encode()).hexdigest()


def sha224(string: str) -> str:
    """Hashes string using sha224 algorithm."""

    return hashlib.sha224(string.encode()).hexdigest()


def sha256(string: str) -> str:
    """Hashes string using sha256 algorithm."""

    return hashlib.sha256(string.encode()).hexdigest()


def sha384(string: str) -> str:
    """Hashes string using sha384 algorithm."""

    return hashlib.sha384(string.encode()).hexdigest()


def sha512(string: str) -> str:
    """Hashes string using sha512 algorithm."""

    return hashlib.sha512(string.encode()).hexdigest()


# ==-----------------------------------------------------------------------------== #
# String functions                                                                  #
# ==-----------------------------------------------------------------------------== #
# NOTE: This function is necessary to use `REGEXP` keyword in SQLite syntax
# Looks like it's not built-in engine to process it... IDK ¯\_(ツ)_/¯
def regexp(pattern: str, string: str) -> bool:
    """Checks if string matches regex pattern"""

    return re.match(pattern, string) is not None


def contains(string: str, substring: str) -> bool:
    """Checks if substring contains in string."""

    return substring in string


def startswith(string: str, substring: str) -> bool:
    """Checks if string starts with substring."""

    return string.startswith(substring)


def endswith(string: str, substring: str) -> bool:
    """Checks if string ends with substring."""

    return string.endswith(substring)


def substring(string: str, start: int, stop: int) -> None:
    """Retrieves substring from string using start and stop indexes."""

    if start != -1 and stop != -1:
        return string[start:stop]

    if start != -1:
        return string[start:]

    return string[:stop]


def random_regexp_string(pattern: str) -> str:
    """Generates random string matching given regexp pattern."""

    if not isinstance(result := exrex.getone(pattern), str):
        raise Exception("Unable to generate string according given pattern")

    return result


def reverse(string: str) -> None:
    """Reverses string."""

    return string[::-1]


def replace(string: str, old: str, new: str, times: int) -> str:
    """Replaces substring in string N times. Replaces all substrings if `times` is `-1`."""

    return string.replace(old, new, times)


def strip(string: str) -> str:
    """Deletes all escape and space chars from the end and start of the string."""

    return str(string).strip()


def to_lower(string: str) -> str:
    """Converts string to lowercase."""

    return string.lower()


def to_upper(string: str) -> str:
    """Converts string to uppercase."""

    return string.upper()


def to_capital(string: str) -> str:
    """Converts first char of the string to uppercase, another ones - to lowecase."""

    return string.capitalize()


# ==-----------------------------------------------------------------------------== #
# Time functions                                                                    #
# ==-----------------------------------------------------------------------------== #
def now_unix() -> int:
    """Retrieves current Unix-time."""

    return int(time.time())


def now_timestamp() -> str:
    """Retrieves current time stamp."""

    return datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")


def unix_from_timestamp(timestamp: str) -> int:
    """Converts times stamo to Unix-time."""

    return int(time.mktime(datetime.datetime.strptime(timestamp, r"%Y-%m-%d %H:%M:%S").timetuple()))


def timestamp_from_unix(unix_time: int) -> str:
    """Converts Unix-time to time stamp."""

    return datetime.datetime.fromtimestamp(unix_time).strftime(r"%Y-%m-%d %H:%M:%S")


def after_unix(format_time_string: str) -> int:
    """Retrieves Unix-time after specified time period."""

    return now_unix() + sum([int(value[:len(value) - 1]) * time_format_map[value[-1]] for value in re.findall(r"[\d]+[smhdwMy]{1}", format_time_string)])


def before_unix(format_time_string: str) -> int:
    """Retrieves Unix-time after specified time period."""

    return now_unix() - sum([int(value[:len(value) - 1]) * time_format_map[value[-1]] for value in re.findall(r"[\d]+[smhdwMy]{1}", format_time_string)])


def after_timestamp(format_time_string: str) -> str:
    """Retrieves time stamp after specified time period."""

    return timestamp_from_unix(after_unix(format_time_string))


def before_timestamp(format_time_string: str) -> str:
    """Retrieves time stamp after specified time period."""

    return timestamp_from_unix(before_unix(format_time_string))


def time_difference(stop_timestamp: str, start_timestamp: str) -> int:
    """Retrieves time difference between two time stamps."""

    return unix_from_timestamp(stop_timestamp) - unix_from_timestamp(start_timestamp)


# ==-----------------------------------------------------------------------------== #
# Reflection                                                                        #
# ==-----------------------------------------------------------------------------== #
def functions() -> str | None:
    """Retrieves list of registered SQL functions."""

    return ", ".join([item.__name__.upper() for item in sql_functions]) if sql_functions else None


def function_documentation(function_name: str) -> str | None:
    """Retrieves function description if function with given name exists."""

    result = [item.__doc__ for item in sql_functions if item.__name__.lower() == function_name.lower()]
    return result[0] if result else None


def function_annotations(function_name: str) -> str | None:
    """Retrieves function types annotations if function with given name exists."""

    if not (result := [item.__annotations__ for item in sql_functions if item.__name__.lower() == function_name.lower()]):
        return

    arguments = [f"{item[0]}{f'<{item[1].__name__}>' if hasattr(item[1], '__name__') else f'<{str(item[1])}>'}" for item in result[0].items() if item[0] != 'return']
    return_value = result[0].get("return", None)

    return f"({', '.join(arguments)}) -> {f'<{return_value.__name__}>' if hasattr(return_value, '__name__') else f'<{str(return_value)}>'}"


# SQL function list
# NOTE: This line of code have to be placed at the end of the code
sql_functions = [item for _, item in dict(globals()).items() if hasattr(item, "__code__")]
