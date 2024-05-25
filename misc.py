import typing
import tomllib
import aiosqlite


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
