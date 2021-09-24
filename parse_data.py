"""Parses client request and checking are valid request and could be processed or not."""

from base64 import b64encode

from typing import Optional, Union

from config import PROTOCOL, ENCODING, RequestVerb, ResponsePhrase


def make_uniq_id(user_name: str) -> str:
    """Make uniq user name id for database file.

    Args:
        user_name (str): user name from request.
    Returns
        (str): encoded user name id.

    """
    encoded_uniq_name = b64encode(user_name.encode(ENCODING)).decode(ENCODING)
    return encoded_uniq_name


def cut_name(message: str) -> str:
    """Cut requestet user name from message from client.

    Args:
        message (str): message from client.
    Returns:
        (str): cutted name.

    """
    name = message.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    return name


def parse_client_request(message: str) -> Optional[tuple]:
    """Parse client request and return RequestVerb, cutted name,
    encoded name and request body from message if request correct
    and could be processed or None if not.

    Args:
        message (str): message from a client.
    Returns:
        Optional[tuple]: response phrase to client.

    """
    if not ' ' in message:
        return None  # Not any spacebars at message.
    if len(message.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) > 30:
        return None  # Length of request > 30.
    if message.split('\r\n', 1)[0].rsplit(' ', 1)[1] != PROTOCOL:
        return None  # Not correct protocol.

    for verb in RequestVerb:
        if message.startswith(verb.value):
            name = cut_name(message)
            encoded_name = make_uniq_id(name)
            request_body = ''.join(message.split('\r\n', 1)[1])
            break  # If found existing request verb.
    else:
        return None  # Not found correct request verb.
    return (verb, name, encoded_name, request_body)


def forms_response_to_client(response: Union[ResponsePhrase, tuple]) -> str:
    """Forms response to client with RKSOK protocol.

    Args:
        response(Union[ResponsePhrase, tuple]): ResponsePhrase with user data or
        only ResponsePhrase for forming response to client.
    Returns:
        (str): Formed string for response to client by RKSOK protocol.
    """
    if type(response) is tuple:
        phrase, user_data = response
        return f'{phrase.value}\r\n{user_data}\r\n\r\n'
    return f'{response.value}\r\n\r\n'
