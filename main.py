import os
import time
import json
import uvicorn
import fastapi
import aiosqlite

# Local imports
import sqlfunctions

from misc import *
from validation import *

# Global and static variables, constants
application = fastapi.FastAPI(docs_url=None)
config = read_toml_config("config.toml")

database_path = config["database"]["file_path"]


# ==-----------------------------------------------------------------------------== #
# Event handlers                                                                    #
# ==-----------------------------------------------------------------------------== #
async def startup() -> None:
    """Event handler, starts every time with script startup."""

    # await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}Started database service")
    await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}Database is ON and accessible on route %lwhite`{config['database']['route']}`")
    await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}Service is avilabe on %lwhitehttp://{config['database']['host']}:{config['database']['port']}")

    # If SQL starup script wasn't found
    if not os.path.exists("startup.sql"):
        await log(rf"%magenta[%now] %yellowWARN%reset:{' ' * 2}SQL script `startup.sql` not found. Create it to execute SQL script on startup")

    else:

        # Executing SQL query
        async with aiosqlite.connect(database_path) as database:

            # Registarting SQL function
            await registrate_sqlite_functions(database, *sqlfunctions.sql_functions)

            # Allowing to use foreign keys
            await database.execute("PRAGMA foreign_keys = ON;")
            await database.commit()

            # Executing startup SQL script
            try:

                with open("startup.sql", "r", encoding="utf-8") as file:
                    await database.executescript(file.read())
                    await database.commit()

            except Exception:
                await log(rf"%magenta[%now] %redERROR%reset:{' '}Error while executing startup SQL script. Fix it and and start the script again")


# ==-----------------------------------------------------------------------------== #
# HTTP / HTTPS routes                                                               #
# ==-----------------------------------------------------------------------------== #
@application.post(config["database"]["route"])
async def execute_sql_handler(request: fastapi.Request) -> fastapi.Response:
    """Route for process SQL queries."""

    # If allowed IP list is not empty and request IP is not allowed
    if config["database"]["allowed_ips"] and request.client.host not in config["database"]["allowed_ips"]:
        await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %greenOK")
        return {"status": "Error", "detail": ["Your IP are not contains in whitelist"]}

    try:

        # Getting request body in JSON format
        body = await request.json()

        # Required request body params and their limitations
        required_params = ["password", "query", "single"]
        required_params_limitations = [
            ((r"(.*)", None, None), list(), str),
            ((r"(.*)", None, None), list(), str),
            (None, list(), bool),
        ]

        # If password list is empty
        if not config["database"]["allowed_passwords"]:
            del required_params[0]
            del required_params_limitations[0]

        # Params validation
        if validation_errors := await validate_params(body, required_params, required_params_limitations):
            await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %redValidation failed")
            return {"status": "Error", "detail": validation_errors}

        # If password is required and password is invalid
        if "password" in required_params and body["password"] not in config["database"]["allowed_passwords"]:
            await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %redInvalid password")
            return {"status": "Error", "detail": ["Invalid password"]}

        # Executing SQL query
        async with aiosqlite.connect(database_path) as database:

            # Registarting SQL function
            await registrate_sqlite_functions(database, *sqlfunctions.sql_functions)

            # Allowing to use foreign keys
            await database.execute("PRAGMA foreign_keys = ON;")
            await database.commit()

            # If executing only one SQL query, not script
            start_time = time.perf_counter()
            if body["single"]:

                async with database.execute(body["query"]) as cursor:
                    description = [column[0] for column in cursor.description] if cursor.description else None
                    data = await cursor.fetchall() if description else None

                await database.commit()

                stop_time = time.perf_counter()
                execution_time = f"{stop_time - start_time:.7f}"

                await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %greenOK")
                return {"status": "OK", "execution_time_secs": execution_time} | ({"columns": description, "data": data} if description else dict())

            await database.executescript(body["query"])
            await database.commit()

            stop_time = time.perf_counter()
            execution_time = f"{stop_time - start_time:.7f}"

            await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %greenOK")
            return {"status": "OK", "execution_time_secs": execution_time}

    except json.decoder.JSONDecodeError:
        await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %redBody parse exception")
        return {"status": "Error", "detail": ["Expected JSON in request body"]}

    except aiosqlite.Error as error:
        await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %redSQLite exception")
        return {"status": "Error", "detail": ["SQLite error: %s" % error]}

    except Exception as error:
        await log(rf"%magenta[%now] %greenINFO%reset:{' ' * 2}{request.client.host}:{request.client.port} - %lwhite'Database accessed' %redInvalid exception")
        return {"status": "Error", "detail": ["Unexpected exception occurred: %s" % error]}


application.add_event_handler("startup", startup)
uvicorn.run(app=application, host=config["database"]["host"], port=config["database"]["port"], log_level="critical")
