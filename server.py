import asyncio
import aiofiles
import aiofiles.os
from base64 import b64encode


PROTOCOL = "РКСОК/1.0"
ENCODING = "UTF-8"
DNU_MSG = "НИПОНЯЛ РКСОК/1.0"
NORMAL = "НОРМАЛДЫКС РКСОК/1.0"
NOT_FND = "НИНАШОЛ РКСОК/1.0"

ru_verbs_list = {"ОТДОВАЙ ": 'GET',
                 "УДОЛИ ": 'DELETE',
                 "ЗОПИШИ ": 'WRITE'}


async def validation_server_request(message: str) -> str:
    """ Requests validation server and return server response.
        Args:
            message (str): Request from client
        Returns:
            str: Decoded response from validation server"""
    reader, writer = await asyncio.open_connection(
        'vragi-vezde.to.digital', 51624)
    request = f"АМОЖНА? {PROTOCOL}\r\n{message}"
    writer.write(request.encode())
    await writer.drain()

    response = await reader.read(1024)
    writer.close()
    await writer.wait_closed()

    return response.decode(ENCODING)


async def parse_client_request(message: str) -> str:
    """ Parsing client request and return ru_verb if request
        could be processed or dnu_msg if not.
        Args:
            message (str): Client request
        Returns:
            str: verb or dnu_msg"""
    if not ' ' in message:
        return DNU_MSG
    if len(message.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) > 30:
        return DNU_MSG
    if message.split('\r\n', 1)[0].rsplit(' ', 1)[1] != PROTOCOL:
        return DNU_MSG

    for ru_verb in ru_verbs_list:
        if message.startswith(ru_verb):
            break
    else:
        return DNU_MSG
    return f'{ru_verb}'


async def get_user(data: str) -> str:
    """ Searching user into data base.
        Args:
            data ([type]): Message from client response.
        Returns:
            str: Response with requested user or not found message"""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]  # Taking name from request string.
    encode_name = b64encode(name.encode("UTF-8")).decode()
    try:
        async with aiofiles.open(f"db/{encode_name}", 'r', encoding='utf-8') as f:
            user_data = await f.read()
        return f'{NORMAL}\r\n{user_data}'
    except (FileExistsError, FileNotFoundError):
        return NOT_FND


async def writing_new_user(data: str) -> str:
    """ Writing new userfile.
        Args:
            data: Data from client response.
        Returns:
            str: Ok message."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    try:
        async with aiofiles.open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return NORMAL
    # If user already exist, just rewrite data.  
    except FileExistsError:
        async with aiofiles.open(f"db/{encode_name}", 'w', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return NORMAL


async def deleting_user(data: str) -> str:
    """ Deleting user from data base.
        Args:
            data ([type]): Data from client response.
        Returns:
            str: Ok message or not found."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    try:
        await aiofiles.os.remove(f"db/{encode_name}")
        return NORMAL
    except (FileExistsError, FileNotFoundError):
        return NOT_FND


async def handle_echo(reader, writer) -> None:
    """ Await client respose and process it.
        Args:
            reader ([type]): Stream to recieve any data from client.
            writer ([type]): Stream to dispatch parsed and processed client data with 
                verifying response from validation server to client."""
    data = await reader.read(1024)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print(f"Received: {message!r} \nfrom {addr!r}")

    response = await parse_client_request(message)
    if not response.startswith('НИПОНЯЛ'):
        valid_response = await validation_server_request(message)

        if valid_response.startswith('МОЖНА'):
            if response == 'ЗОПИШИ ':
                response = await writing_new_user(message)
            elif response == 'ОТДОВАЙ ':
                response = await get_user(message)
            elif response == 'УДОЛИ ':
                response = await deleting_user(message)
        else:
            # If validation server not allow process client request.
            response = valid_response

    writer.write(response.encode('utf-8'))
    await writer.drain()
    print("\nClose the connection with client")
    writer.close()


async def main():
    server = await asyncio.start_server(
        handle_echo, '0.0.0.0', 3389)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}\n')
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
