"""RKSOK protocol server. For token test"""
import asyncio
from logging import debug
import aiofiles
from aiofiles.os import remove
from base64 import b64encode
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
    logger.debug(request)  # State of request to server
    writer.write(f"{request}\r\n\r\n".encode())
    await writer.drain()

    response = await reader.readline()
    writer.close()
    await writer.wait_closed()

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
    logger.debug(f'GET_USER\r\n{name}\r\n{encode_name}')
    try:
        async with aiofiles.open(f"db/{encode_name}", 'r', encoding='utf-8') as f:
            user_data = await f.read()
        logger.debug(f'GET_USER RESPONSE\r\n{response_phrases["OK"]}\r\n{user_data}')
        return f'{response_phrases["OK"]}\r\n{user_data}'
    except (FileExistsError, FileNotFoundError):
        return response_phrases["N_FND"]


async def writing_new_user(data: str) -> str:
    """Write new userfile.

    Args:
        data: Data from client response.
    Returns:
        str: Ok message. 

    """
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode(ENCODING)).decode()
    logger.debug(f'WRITING_NEW_USER\r\n{name}\r\n{encode_name}')
    try:
        async with aiofiles.open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return response_phrases["OK"]
    except FileExistsError:  # If user already exist, just rewrite data.  
        async with aiofiles.open(f"db/{encode_name}", 'w', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return response_phrases["OK"]


async def deleting_user(data: str) -> str:
    """Delete user from data base.

    Args:
        data: Data from client response.
    Returns:
        str: Response ok phrase or not found. 

    """
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode(ENCODING)).decode()
    logger.debug(f'DELETING_USER\r\n{name}\r\n{encode_name}')
    try:
        await remove(f"db/{encode_name}")
        return response_phrases["OK"]
    except (FileExistsError, FileNotFoundError):
        return response_phrases["N_FND"]


async def handle_echo(reader, writer) -> None:
    """Await client respose and process it.

    Args:
        reader: Stream to recieve any data from client.
        writer: Stream to dispatch parsed and processed client data with
                verifying response from validation server to client. 

    """
    data = await reader.readline()
    message = data.decode()
    logger.debug(message)  # State of request message from client
    addr = writer.get_extra_info('peername')
    print(f"Received: {message!r} \nfrom {addr!r}")

    response = await parse_client_request(message)
    if not response.startswith('НИПОНЯЛ'):
        valid_response = await validation_server_request(message)
        logger.debug(valid_response)  # State of response from server

        if valid_response.startswith('МОЖНА'):
            if response == 'ЗОПИШИ ':
                response = await writing_new_user(message)
            elif response == 'ОТДОВАЙ ':
                response = await get_user(message)
            elif response == 'УДОЛИ ':
                response = await deleting_user(message)
        else:  # If validation server not allow process client request.
            response = valid_response

    logger.debug(response)  # State of not valid response from client 
    writer.write(f"{response}\r\n\r\n".encode(ENCODING))
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
