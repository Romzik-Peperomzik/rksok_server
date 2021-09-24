"""RKSOK protocol server."""

import asyncio
import sys
import traceback

from loguru import logger

from config import ENCODING, RequestVerb, ResponsePhrase
from parse_data import parse_client_request, forms_response_to_client
from process_data import write_new_user, get_user, delete_user
from validation import validation_server_request


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
    decoded_message = data.decode(ENCODING)
    addr = writer.get_extra_info('peername')
    logger.debug(f'\nRECEIVED FROM: {addr}:\nENCODED:\n{data}\nDECODED:\n{decoded_message}\n')

    parsed_request = parse_client_request(decoded_message)
    if parsed_request:
        requested_verb, name, encoded_name, request_body = parsed_request
        validation_server_response = await validation_server_request(decoded_message)

        if validation_server_response.startswith(ResponsePhrase.APPR.value):
            if requested_verb == RequestVerb.GET:
                processed_client_request = await get_user(name, encoded_name)
            elif requested_verb == RequestVerb.WRITE:
                processed_client_request = await write_new_user(request_body, name, encoded_name)
            elif requested_verb == RequestVerb.DELETE:
                processed_client_request = await delete_user(name, encoded_name)
            response_to_client = forms_response_to_client(processed_client_request)
        else:  # If validation server not allow process client request.
            response_to_client = validation_server_response
    else:  # Not correct request from client.
        response_to_client = forms_response_to_client(ResponsePhrase.DNU)

    writer.write(f"{response_to_client}".encode(ENCODING))
    await writer.drain()
    writer.close()
    logger.debug(f'\nRESPONSE_TO_CLIENT:\n{response_to_client}')


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
