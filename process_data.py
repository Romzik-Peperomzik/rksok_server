"""Process data from requests."""

from typing import Union

import aiofiles
from aiofiles.os import remove
from loguru import logger

from config import ResponsePhrase



async def get_user(name: str, encoded_name:str) -> Union[ResponsePhrase, tuple]:
    """Search user into database.

    Args:
        name(str): Name from client request.
        encoded_name(str): Unique id based on encoded user name for file name.
    Returns:
        Union[ResponsePhrase, tuple]: OK phrase and user_data from file.
        
    """
    logger.debug(f'\nGET_USER_FROM_DB:\nNAME:{name}\nENCODED_NAME:{encoded_name}\n')
    try:
        async with aiofiles.open(f"db/{encoded_name}", 'r', encoding='utf-8') as f:
            user_data = await f.read()
        logger.debug(f'\nGET_USER_RESPONSE_FULL_DATA:\n{ResponsePhrase.OK.value}\n{user_data}')
        return (ResponsePhrase.OK, user_data)

    except (FileExistsError, FileNotFoundError):
        return ResponsePhrase.N_FND


async def write_new_user(request_body: str, name: str, encoded_name: str) -> ResponsePhrase:
    """Write new userfile.

    Args:
        request_body(str): Body data from client response.
        name(str): Name from client request.
        encoded_name(str): Unique id for file name.
    Returns:
        ResponsePhrase: OK phrase.

    """
    logger.debug(f'\nWRITING_NEW_USER_NAME\nNAME:{name}\nENCODED_NAME:{encoded_name}\n')
    logger.debug(f'\nWRITING_NEW_USER_BODY:\n{request_body}')
    try:
        async with aiofiles.open(f"db/{encoded_name}", 'x', encoding='utf-8') as f:
            await f.write(request_body)
        return ResponsePhrase.OK

    except FileExistsError:  # If user already exist, rewrite message.
        async with aiofiles.open(f"db/{encoded_name}", 'w', encoding='utf-8') as f:
            await f.write(request_body)
        return ResponsePhrase.OK


async def delete_user(name: str, encoded_name:str) -> ResponsePhrase:
    """Delete user from database.

    Args:
        name(str): Name from client request.
        encoded_name(str): Unique id for file name.
    Returns:
        ResponsePhrase: OK or Not Found phrase.

    """
    logger.debug(f'\nDELETING_USER_NAME_ENCODED_NAME:\n{name}\n{encoded_name}')
    try:
        await remove(f"db/{encoded_name}")
        return ResponsePhrase.OK

    except (FileExistsError, FileNotFoundError):
        return ResponsePhrase.N_FND
