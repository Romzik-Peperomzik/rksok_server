import socket
from enum import Enum


class CanNotParseResponseError(Exception):
    """ Error that occurs when we can not parse some strange
        response from RKSOK client."""
    pass


ru_verbs_list = {"ОТДОВАЙ": 'GET',
                 "УДОЛИ": 'DELETE',
                 "ЗОПИШИ": 'WRITE'}

PROTOCOL = "РКСОК/1.0"
ENCODING = "UTF-8"  

def parse_response(conn: str) -> str:
    """ Processing client response
        Args:
            raw_response (str): Запрос.
        Raises:
            CanNotParseResponseError: Ошибка если команду запроса неудалось обработать.
        Returns:
            str: [description]"""    
    data = f'{conn.recv(1024).decode(ENCODING)}'
    for ru_verb in ru_verbs_list:
        if data.startswith(ru_verb):
            break
    else:
        raise CanNotParseResponseError()  

    validation_request = get_validation_body(data)
    return send_valid_request(validation_request)
    

def get_validation_body(decoded_data: str) -> bytes:
    """ Composes validation request.
        Args:
            decoded_data (str): [description]
        Returns:
            bytes: Encoded request"""
    request = f"АМОЖНА? {PROTOCOL}\r\n{decoded_data}"
    request += "\r\n"
    return request.encode(ENCODING)


def send_valid_request(request_body: bytes) -> str:
    """ Send validation request and receive valid response.
        Args:
            request_body (bytes): Body request.
        Returns:
            str: Decoded valid response."""
    valid_conn = socket.create_connection(('vragi-vezde.to.digital', 51624))
    valid_conn.sendall(request_body)
    valid_response = receive_response_body(valid_conn)
    return valid_response  


def receive_response_body(valid_conn) -> str:
        """ Receives data from socket connection and returns it as string,
            decoded using ENCODING"""
        response = b""
        while True:
            data = valid_conn.recv(1024)
            if not data: break
            response += data
        return response.decode(ENCODING)  # Возвращаем декодированный ответ от сервера.

def run_server() -> None:
    """Waiting for a client and proceed client request."""
    server = socket.create_server(("0.0.0.0", 3333))  # Принимаем любые запросы этой машины на порт 3333.
    server.listen(1)  # Длина очереди.
    print('Waiting for connection...')
    conn, addr = server.accept()  # Объект для работы с клиентским сокетом. Адрес клиента.
    print('Got new connection')
    valid_or_not_response = parse_response(conn)

    if valid_or_not_response.startswith('МОЖНА'):
        # Опиши логику если можно обработать
        response = f'НОРМАЛДЫКС РКСОК/1.0\r\n812334554\r\n\r\n'
        conn.send(response.encode(ENCODING))
        conn.shutdown(socket.SHUT_RDWR)
    else:
        # А здесь если нельзя
        pass
    
# server.close()