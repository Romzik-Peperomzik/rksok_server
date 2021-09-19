"""RKSOK protocol server."""

import asyncio
from base64 import b64encode
import sys
import traceback

import aiofiles
from aiofiles.os import remove
from config import PROTOCOL, ENCODING, VALIDATION_SERVER_URL,\
                   VALIDATION_SERVER_PORT, RequestVerb, ResponsePhrase
from loguru import logger


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


async def validation_server_request(message: str) -> str:
    """Request to validation server and return server response.

    Args:
        message: Request from client.
    Returns:
        str: Decoded response from validation server.

    """
    reader, writer = await asyncio.open_connection(
        VALIDATION_SERVER_URL, VALIDATION_SERVER_PORT)

    request = f"АМОЖНА? {PROTOCOL}\r\n{message}"
    writer.write(f"{request}\r\n\r\n".encode(ENCODING))
    await writer.drain()
    response = b''
    while True:  # reading all data from validation server by 1kb blocks
        line = await reader.read(1024)
        response += line
        if response.endswith(b'\r\n\r\n') or not line:
            break
    writer.close()
    await writer.wait_closed()
    logger.debug(f'\nREQUEST_TO_VALIDATION_SERVER:\n{request}')
    logger.debug(f'\nRESPONSE_FROM_VALIDATION_SERVER:\n{response.decode(ENCODING)}')
   
    return response.decode(ENCODING)


def parse_client_request(message: str) -> str:
    """Parse client request and return verb if request could be 
    processed or Do_Not_Understand phrase if not.

    Args:
        message (str): message from a client.
    Returns:
        str: response phrase to client.

    """
    if not ' ' in message:
        return f'{ResponsePhrase.DNU.value}\r\n\r\n'  # Not any spacebars at message.
    if len(message.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) > 30:
        return f'{ResponsePhrase.DNU.value}\r\n\r\n'  # Length of response > 30.
    if message.split('\r\n', 1)[0].rsplit(' ', 1)[1] != PROTOCOL:
        return f'{ResponsePhrase.DNU.value}\r\n\r\n'  # Not correct protocol.

    for verb in RequestVerb:
        if message.startswith(verb.value):
            break  # If found existing request verb.
    else:
        return f'{ResponsePhrase.DNU.value}\r\n\r\n'  # Not found correct request verb.
    return verb


async def process_client_request(reader, writer):
    """Await client response and process it.

    Args:
        reader: A stream to recieve any data from client.
        writer: A stream to dispatch parsed and processed client data. 

    """
    data = b''
    while True:  # reading all data from client by 1kb blocks
        line = await reader.read(1024)
        data += line
        if data.endswith(b'\r\n\r\n') or not line:
            break
    addr = writer.get_extra_info('peername')    
    message = data.decode(ENCODING)
    logger.debug(f'\nRECEIVED FROM: {addr}:\nENCODED:\n{data}\nDECODED:\n{message}\n')

    response = parse_client_request(message)
    if not response == f'{ResponsePhrase.DNU.value}\r\n\r\n':
        valid_response = await validation_server_request(message)

        if valid_response.startswith(ResponsePhrase.APPR.value):
            if response == RequestVerb.WRITE:
                response = await write_new_user(message)
            elif response == RequestVerb.GET:
                response = await get_user(message)
            elif response == RequestVerb.DELETE:
                response = await delete_user(message)
        else:  # If validation server not allow process client request.
            response = valid_response

    writer.write(f"{response}".encode(ENCODING))
    await writer.drain()
    writer.close()
    logger.debug(f'\nRESPONSE_TO_CLIENT:\n{response}')


async def turn_on_server():
    """Start server and print address of new connection."""
    addr, port = sys.argv[1], int(sys.argv[2])  # get address and port from command line arguments.

    server = await asyncio.start_server(
        process_client_request, addr, port)
    print(f'Serving on {addr}\n')
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    logger.add("logs/debug.log", format="{time} {level} {message}")
    try:
        asyncio.run(turn_on_server())
    except KeyboardInterrupt:
        print('\nKeyboard interrupt: Server shutdown!')
    except Exception:
        tb = traceback.format_exc()
        logger.critical(f"Traceback:\n{tb}")
        pass
