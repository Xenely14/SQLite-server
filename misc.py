import typing
import asyncio
import tomllib
import colorama
import datetime
import aiosqlite

# Global and static variables, constants
log_formatations_map = {
    r"%now": datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S"),

    r"%lred": colorama.Fore.LIGHTRED_EX,
    r"%lgreen": colorama.Fore.GREEN,
    r"%lblue": colorama.Fore.LIGHTBLUE_EX,
    r"%lyellow": colorama.Fore.LIGHTYELLOW_EX,
    r"%lmagenta": colorama.Fore.LIGHTMAGENTA_EX,
    r"%lcyan": colorama.Fore.LIGHTCYAN_EX,
    r"%lwhite": colorama.Fore.LIGHTWHITE_EX,
    r"%lblack": colorama.Fore.LIGHTBLACK_EX,

    r"%red": colorama.Fore.RED,
    r"%green": colorama.Fore.GREEN,
    r"%blue": colorama.Fore.BLUE,
    r"%yellow": colorama.Fore.YELLOW,
    r"%magenta": colorama.Fore.MAGENTA,
    r"%cyan": colorama.Fore.CYAN,
    r"%white": colorama.Fore.WHITE,
    r"%black": colorama.Fore.BLACK,

    r"%reset": colorama.Fore.RESET
}


# ==------------------------------------------------------------== #
# Functions                                                        #
# ==------------------------------------------------------------== #
def read_toml_config(filename: str) -> dict[str, typing.Any]:
    """Reads TOML config file."""

    if not filename.endswith(".toml"):
        raise Exception("Config is have to be `toml` format")

    with open(filename, "rb") as file:
        config = tomllib.load(file)

    return config


# ==------------------------------------------------------------== #
# Async function                                                   #
# ==------------------------------------------------------------== #
async def log(message: str, autoreset: bool = True) -> None:
    """Prints formated log message."""

    finally_message = message
    for formatation in log_formatations_map:

        finally_message = finally_message.replace(formatation, log_formatations_map[formatation])
        await asyncio.sleep(0)

    if autoreset:
        finally_message += log_formatations_map[r"%reset"]

    print(finally_message)


async def registrate_sqlite_functions(database: aiosqlite.Connection, *functions: callable) -> None:
    """Registrates list of functions to make it callable from SQL syntax."""

    for function in functions:

        # Deleting return value from function types annotations if it's exists
        if "return" in (function_annotations := function.__annotations__.copy()):
            del function_annotations["return"]

        # If not all of the function arguments have types annotations
        if function.__code__.co_argcount != len(function_annotations):
            raise Exception(f"All `{function.__name__}` function arguments have to be annotated")

        # SQLite function registration
        await database.create_function(function.__name__.upper(), len(function_annotations), function)
