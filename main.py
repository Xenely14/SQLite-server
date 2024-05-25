import os
import time
import json
import uvicorn
import fastapi
import datetime
import colorama
import aiosqlite

# Local imports
import sqlfunctions

from misc import *
from validation import *

# Global and static variables, constants
DATABASE_PATH = "database.db"

application = fastapi.FastAPI(docs_url=None)
config = read_toml_config("config.toml")

fore = colorama.Fore


# ==-----------------------------------------------------------------------------== #
# Middleware                                                                        #
# ==-----------------------------------------------------------------------------== #
@application.middleware("http")
async def log_middleware(request: fastapi.Request, next: typing.Coroutine) -> fastapi.Response:

    # If route are not regisered
    if request.url.path not in [item.path for item in application.routes]:
        return

    return await next(request)


# ==-----------------------------------------------------------------------------== #
# Event handlers                                                                    #
# ==-----------------------------------------------------------------------------== #
async def startup() -> None:
    """Event handler, starts every time with script startup."""

    print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.GREEN}INFO{fore.RESET}:{' ' * 2}Started database service")
    print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.GREEN}INFO{fore.RESET}:{' ' * 2}Database is ON and accessible on route {fore.LIGHTWHITE_EX}`{config["database"]["route"]}`{fore.RESET}")

    # If SQL starup script wasn't found
    if not os.path.exists("startup.sql"):
        print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.YELLOW}WARN{fore.RESET}:{' ' * 2}SQL script `startup.sql` not found. Create it to execute SQL script on startup")

    else:

        async with aiosqlite.connect(DATABASE_PATH) as database:

            # Registarting SQL function
            await registrate_sqlite_functions(database, *sqlfunctions.sql_functions)

            # Allowing to use foreign keys
            await database.execute("PRAGMA foreign_keys = ON;")
            await database.commit()

            # Executing startup SQL script
            with open("startup.sql", "r", encoding="utf-8") as file:
                await database.executescript(file.read())
                await database.commit()


# ==-----------------------------------------------------------------------------== #
# HTTP / HTTPS routes                                                               #
# ==-----------------------------------------------------------------------------== #
@application.post(config["database"]["route"])
async def execute_sql_handler(request: fastapi.Request) -> fastapi.Response:
    """Route for process SQL queries."""

    # If allowed IP list is not empty and request IP is not allowed
    if config["database"]["allowed_ips"] and request.client.host not in config["database"]["allowed_ips"]:
        print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.RED}ERROR{fore.RESET}:{' ' * 1}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} rejected, IP not allowed")
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
            print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.RED}ERROR{fore.RESET}:{' ' * 1}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} rejected, validation failed")
            return {"status": "Error", "detail": validation_errors}

        # If password is required and password is invalid
        if "password" in required_params and body["password"] not in config["database"]["allowed_passwords"]:
            print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.RED}ERROR{fore.RESET}:{' ' * 1}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} rejected, invalid password {fore.LIGHTWHITE_EX}`{body['password']}{fore.RESET}`")
            return {"status": "Error", "detail": ["Invalid password"]}

        # Executing SQL query
        async with aiosqlite.connect(DATABASE_PATH) as database:

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

                print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.GREEN}INFO{fore.RESET}:{' ' * 2}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} accessed database successfully")
                return {"status": "OK", "execution_time_secs": execution_time} | ({"columns": description, "data": data} if description else dict())

            await database.executescript(body["query"])
            await database.commit()

            stop_time = time.perf_counter()
            execution_time = f"{stop_time - start_time:.7f}"

            print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.GREEN}INFO{fore.RESET}:{' ' * 2}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} accessed database successfully`")
            return {"status": "OK", "execution_time_secs": execution_time}

    except json.decoder.JSONDecodeError:
        print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.RED}ERROR{fore.RESET}:{' ' * 1}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} rejected, JSON parse error in body")
        return {"status": "Error", "detail": ["Expected JSON in request body"]}

    except aiosqlite.Error as error:
        print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.RED}ERROR{fore.RESET}:{' ' * 1}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} rejected, SQLite error")
        return {"status": "Error", "detail": ["SQLite error: %s" % error]}

    except Exception as error:
        print(f"{fore.LIGHTMAGENTA_EX}[{datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")}] {fore.RED}ERROR{fore.RESET}:{' ' * 1}Client {fore.LIGHTWHITE_EX}{request.client.host}:{request.client.port}{fore.RESET} rejected, unexpected exception occurred")
        return {"status": "Error", "detail": ["Unexpected exception occurred: %s" % error]}


application.add_event_handler("startup", startup)
uvicorn.run(app=application, host=config["database"]["host"], port=config["database"]["port"], log_level="critical")
