import re
import typing
import asyncio

# Local imports
from misc import *


# ==------------------------------------------------------------== #
# Functions                                                        #
# ==------------------------------------------------------------== #
def validate_string(string: str, pattern: str, min_length: int = None, max_length: int = None) -> str | None:
    """Checks if string have valid size and regexp pattern."""

    # If string size is invalid
    if min_length and max_length and min_length == max_length and len(string) != min_length:
        return "have to be `%s` char(s)" % min_length

    # If string size less allowed
    if min_length and len(string) < min_length:
        return "too short, have to be at least `%s` char(s)" % min_length

    # If string size greater allowed
    if max_length and len(string) > max_length:
        return "too long, have be at most `%s` char(s)" % max_length

    # If string doesn't matches regexp pattern
    if not re.match(pattern, string):
        return "doesn't matches `%s` limitation pattern" % pattern.replace("\\", r"\\", -1)


def validate_range(value: int | float, min_value: int | float = None, max_value: int | float = None) -> str | None:
    """Checks if number are in valid ranges."""

    # If number are not in valid ranges
    if min_value is not None and max_value is not None and not min_value <= value <= max_value:
        return "have to be in range from `%s` to `%s` inclusive" % (f"{min_value:_}", f"{max_value:_}")

    # If number less than allowed
    if min_value is not None and value < min_value:
        return "have to be greater than `%s`" % f"{min_value:_}"

    # If number greater than allowed
    if max_value is not None and value > max_value:
        return "have to be less than `%s`" % f"{max_value:_}"


# ==------------------------------------------------------------== #
# Async functions                                                  #
# ==------------------------------------------------------------== #
async def validate_params(params: dict[str, typing.Any], required_params: list[str], params_limitations: list[tuple[tuple | None, list | None, type]]) -> list[str]:
    """Checks if all required params were received and validates them."""

    missing_params = list()
    invalid_params = list()

    # Params validation
    for required_param, param_limitation in zip(required_params, params_limitations):

        # Если обязательный параметр не был получен
        if required_param not in params:
            missing_params.append("Param `%s` required but not received" % required_param)

            await asyncio.sleep(0)
            continue

        else:

            # If params type is invalid
            if not isinstance(params[required_param], param_limitation[2]):
                invalid_params.append("Param `%s` have to be `%s` type" % (required_param, param_limitation[2].__name__))

                await asyncio.sleep(0)
                continue

            # If param are not in enumeration of allowed params
            if param_limitation[1] and params[required_param] not in param_limitation[1]:
                invalid_params.append("Param `%s` can only have one of the values: %s" % (required_param, ", ".join([f"'{item}'" for item in param_limitation[1]])))

                await asyncio.sleep(0)
                continue

            # Validating by length and regexp pattern
            if not param_limitation[1] and param_limitation[0]:

                # If param is number
                if type(param := params[required_param]) in [int, float]:

                    if range_error := validate_range(param, *param_limitation[0]):
                        invalid_params.append("Param `%s` %s" % (required_param, range_error))

                # If param is string
                else:

                    if match_error := validate_string(param, *param_limitation[0]):
                        invalid_params.append("Param `%s` %s" % (required_param, match_error))

        await asyncio.sleep(0)

    return [*missing_params, *invalid_params]
