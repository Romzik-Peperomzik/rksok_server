"""Parses client request and checking are valid request and could be processed or not."""

from config import PROTOCOL, RequestVerb, ResponsePhrase


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
