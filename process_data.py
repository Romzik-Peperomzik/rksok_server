"""Process data from requests."""

from base64 import b64encode

import aiofiles
from aiofiles.os import remove
from loguru import logger

from config import ENCODING, ResponsePhrase


def make_uniq_id(user_name: str) -> str:
    """Make uniq user name id for database file.

    Args:
        user_name (str): user name from request.
    Returns:
        b64encode: decoded user name id.

    """
    encoded_uniq_name = b64encode(user_name.encode(ENCODING)).decode(ENCODING)
    return encoded_uniq_name


def cut_name(message: str) -> str:
    """Cut requestet user name from message from client.

    Args:
        message (str): message from client.
    Returns:
        str: cutted name.

    """
    name = message.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    return name


async def get_user(data: str) -> str:
    """Search user into database.

    Args:
        data: Message from client response.
    Returns:
        str: Response with requested user or not found message.

    """
    name = cut_name(data)
    encoded_name = make_uniq_id(name)
    logger.debug(f'\nGET_USER_FROM_DB:\nNAME:{name}\nENCODED_NAME:{encoded_name}\n')
    try:
        async with aiofiles.open(f"db/{encoded_name}", 'r', encoding='utf-8') as f:
            user_data = await f.read()
        logger.debug(f'\nGET_USER_RESPONSE_FULL_DATA:\n{ResponsePhrase.OK.value}\n{user_data}')
        return f'{ResponsePhrase.OK.value}\r\n{user_data}\r\n\r\n'
    except (FileExistsError, FileNotFoundError):
        return f'{ResponsePhrase.N_FND.value}\r\n\r\n'


async def write_new_user(data: str) -> str:
    """Write new userfile.

    Args:
        data: Data from client response.
    Returns:
        str: Ok message.

    """
    name = cut_name(data)
    encoded_name = make_uniq_id(name)
    logger.debug(f'\nWRITING_NEW_USER_NAME\nNAME:{name}\nENCODED_NAME:{encoded_name}\n')
    logger.debug(f'\nWRITING_NEW_USER FULL DATA:\n{data}')
    try:
        async with aiofiles.open(f"db/{encoded_name}", 'x', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return f'{ResponsePhrase.OK.value}\r\n\r\n'
    except FileExistsError:  # If user already exist, rewrite data.
        async with aiofiles.open(f"db/{encoded_name}", 'w', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return f'{ResponsePhrase.OK.value}\r\n\r\n'


async def delete_user(data: str) -> str:
    """Delete user from database.

    Args:
        data: Data from client response.
    Returns:
        str: Response OK or Not Found phrase.

    """
    name = cut_name(data)
    encoded_name = make_uniq_id(name)
    logger.debug(f'\nDELETING_USER_NAME_ENCODED_NAME:\n{name}\n{encoded_name}')
    try:
        await remove(f"db/{encoded_name}")
        return f'{ResponsePhrase.OK.value}\r\n\r\n'
    except (FileExistsError, FileNotFoundError):
        return f'{ResponsePhrase.N_FND.value}\r\n\r\n'
