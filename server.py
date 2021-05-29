import socket
from enum import Enum
from base64 import b64encode

PROTOCOL = "РКСОК/1.0"
ENCODING = "UTF-8" 


class CanNotParseResponseError(Exception):
    """ Error that occurs when we can not parse some strange
        response from RKSOK client."""
    pass


ru_verbs_list = {"ОТДОВАЙ": 'GET',
                 "УДОЛИ": 'DELETE',
                 "ЗОПИШИ": 'WRITE'}

 
def parse_response(data: str) -> str:
    """ Processing client response
        Args:
            raw_response (str): Запрос.
        Raises:
            CanNotParseResponseError: Ошибка если команду запроса неудалось обработать.
        Returns:
            str: [description]"""    
    for ru_verb in ru_verbs_list:  # Узнаём какая именно команда пришла.
        if data.startswith(ru_verb):
            break
    else:
        raise CanNotParseResponseError()  

    validation_request = get_validation_body(data)  # Идём узнавать у сервера проверки.
    validation_response = send_validation_request(validation_request)
    print('Всё проверил, можно падать.')
    if validation_response.startswith('МОЖНА') and \
    len(data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) <= 30:    
        response = f'НОРМАЛДЫКС РКСОК/1.0\r\n\r\n'
        if ru_verb == 'ЗОПИШИ':
            writing_new_user(data)
            return response
        elif ru_verb == 'ОТДОВАЙ':
            pass
        else:
            pass
                
    else:
        
        pass


def writing_new_user(data):
    """ Writing new userfile.
        Args:
            data: Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    print(encode_name)
    with open(f"{encode_name}", 'x', encoding='utf-8') as f:
        f.write(data.split('\r\n', 1)[1])


def get_validation_body(decoded_data: str) -> bytes:
    """ Composes validation request.
        Args:
            decoded_data (str): [description]
        Returns:
            bytes: Encoded request"""
    request = f"АМОЖНА? {PROTOCOL}\r\n{decoded_data}"
    request += "\r\n"  #TODO: Надо понять нужен ли тут доп. отступ.
    return request.encode(ENCODING)


def send_validation_request(request_body: bytes) -> str:
    """ Send validation request and receive valid response.
        Args:
            request_body (bytes): Body request.
        Returns:
            str: Decoded valid response."""
    valid_conn = socket.create_connection(('0.0.0.0', 3332))  # ('vragi-vezde.to.digital', 51624)
    valid_conn.sendall(request_body)
    valid_response = receive_validation_response(valid_conn)
    return valid_response  


def receive_validation_response(valid_conn) -> str:
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
    data = f'{conn.recv(1024).decode(ENCODING)}'
    valid_or_not_response = parse_response(data)

    conn.send(valid_or_not_response.encode(ENCODING))
    conn.shutdown(socket.SHUT_RDWR)
    
    
if __name__ == '__main__':
    run_server()