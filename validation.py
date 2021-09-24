"""Sends a validation request to validation server and receives answer, could be request processed or not."""
import asyncio

from loguru import logger

from config import PROTOCOL, ENCODING, VALIDATION_SERVER_URL, VALIDATION_SERVER_PORT


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
