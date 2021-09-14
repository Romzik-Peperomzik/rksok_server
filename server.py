"""RKSOK protocol server. For token test"""
import asyncio
from logging import debug
import aiofiles
from aiofiles.os import remove
from base64 import b64encode
from asyncio.tasks import current_task
from loguru import logger


PROTOCOL = "РКСОК/1.0"
ENCODING = "UTF-8"

request_verbs = ["ОТДОВАЙ ", "УДОЛИ ", "ЗОПИШИ "]

response_phrases = {"N_FND": "НИНАШОЛ РКСОК/1.0",
                      "DNU": "НИПОНЯЛ РКСОК/1.0",
                       "OK": "НОРМАЛДЫКС РКСОК/1.0"}


async def validation_server_request(message: str) -> str:
    """Request validation server and return server response.

    Args: 
        message: Request from client
    Returns: 
        str: Decoded response from validation server

    """
    reader, writer = await asyncio.open_connection(
        'vragi-vezde.to.digital', 51624)
    request = f"АМОЖНА? {PROTOCOL}\r\n{message}"
    logger.debug(f'\nREQUEST_TO_VALID_SERVER:\r\n{request}')
    writer.write(f"{request}\r\n\r\n".encode())
    await writer.drain()
    
    response = str()
    while current_line != '\r\n':
        current_line = await reader.readline()
        response += current_line
    # response = await reader.readuntil(separator=b'\r\n\r\n')
    writer.close()
    await writer.wait_closed()

    # h_r_response = response.decode(ENCODING)
    # logger.debug(f'RESPONSE_FROM_VALID_SERVER:\r\n{h_r_response}')
    return response.decode(ENCODING)


async def parse_client_request(message: str) -> str:
    """Parse client request and return verb if request could be processed or dnu_msg if not.

    Args:
        message (str): message from a client.

    Returns:
        str: response phrase to client.

    """
    if not ' ' in message:
        return response_phrases["DNU"]
    if len(message.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) > 30:
        return response_phrases["DNU"]
    if message.split('\r\n', 1)[0].rsplit(' ', 1)[1] != PROTOCOL:
        return response_phrases["DNU"]

    for verb in request_verbs:
        if message.startswith(verb):
            break  # If find existing verb just break.
    else:
        return response_phrases["DNU"]
    return f'{verb}'


async def get_user(data: str) -> str:
    """Search user into data base.

    Args:
        data: Message from client response.
    Returns:
        str: Response with requested user or not found message.

    """
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]  # Taking name from request string.
    encode_name = b64encode(name.encode(ENCODING)).decode()
    logger.debug(f'\nGET_USER_FROM_DB\r\n{name}\r\n{encode_name}')
    try:
        async with aiofiles.open(f"db/{encode_name}", 'r', encoding='utf-8') as f:
            user_data = await f.read()
        logger.debug(f'\nGET_USER RESPONSE\r\n{response_phrases["OK"]}\r\n{user_data}')
        return f'{response_phrases["OK"]}\r\n{user_data}\r\n\r\n'
    except (FileExistsError, FileNotFoundError):
        return f'{response_phrases["N_FND"]}\r\n\r\n'


async def writing_new_user(data: str) -> str:
    """Write new userfile.

    Args:
        data: Data from client response.
    Returns:
        str: Ok message. 

    """
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode(ENCODING)).decode()
    logger.debug(f'\nWRITING_NEW_USER_NAME\r\n{name}\r\n{encode_name}')
    logger.debug(f'\nWRITING_NEW_USER FULL DATA\r\n{data}')
    try:
        async with aiofiles.open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return f'{response_phrases["OK"]}\r\n\r\n'
    except FileExistsError:  # If user already exist, just rewrite data.  
        async with aiofiles.open(f"db/{encode_name}", 'w', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return f'{response_phrases["OK"]}\r\n\r\n'


async def deleting_user(data: str) -> str:
    """Delete user from data base.

    Args:
        data: Data from client response.
    Returns:
        str: Response ok phrase or not found. 

    """
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode(ENCODING)).decode()
    logger.debug(f'\nDELETING_USER_NAME_ENCODE_NAME\r\n{name}\r\n{encode_name}')
    try:
        await remove(f"db/{encode_name}")
        return f'{response_phrases["OK"]}\r\n\r\n'
    except (FileExistsError, FileNotFoundError):
        return f'{response_phrases["N_FND"]}\r\n\r\n'


async def handle_echo(reader, writer) -> None:
    """Await client respose and process it.

    Args:
        reader: Stream to recieve any data from client.
        writer: Stream to dispatch parsed and processed client data with
                verifying response from validation server to client. 

    """
    data = str()
    while current_line != '\r\n':
        current_line = await reader.readline()
        data += current_line
    # data = await reader.readuntil(separator=b'\r\n\r\n')
    message = data.decode()
    logger.debug(f'\nUSER_REQUESTED_DATA:\r\n{message}')
    addr = writer.get_extra_info('peername')
    print(f"Received: {message!r} \nfrom {addr!r}")

    response = await parse_client_request(message)
    if response.startswith('НИПОНЯЛ'):
        response = f'{response}\r\n\r\n'
    else:
        valid_response = await validation_server_request(message)

        if valid_response.startswith('МОЖНА'):
            if response == 'ЗОПИШИ ':
                response = await writing_new_user(message)
            elif response == 'ОТДОВАЙ ':
                response = await get_user(message)
            elif response == 'УДОЛИ ':
                response = await deleting_user(message)
        else:  # If validation server not allow process client request.
            response = valid_response

    logger.debug(f'\nRESPONSE_TO_CLIENT\r\n{response}')
    writer.write(f"{response}".encode(ENCODING))
    await writer.drain()
    print("\nClose the connection with client\n\n")
    writer.close()


async def main() -> None:
    """Start server and print addres of new connection."""
    server = await asyncio.start_server(
        handle_echo, '0.0.0.0', 3900)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}\n')
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    logger.add("debug.log", format="{time} {level} {message}")
    asyncio.run(main())
