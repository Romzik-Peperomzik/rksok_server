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

    validation_request = get_validation_body(data)  # Формируем запрос для сервера проверки.
    validation_response = send_validation_request(validation_request)  # Идём узнавать у сервера проверки.
    print('\nОтвет от сервера валидации получен.')
    
    if validation_response.startswith('МОЖНА') and \
    len(data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) <= 30:    
        response = f'НОРМАЛДЫКС РКСОК/1.0'
        if ru_verb == 'ЗОПИШИ':
            print('Дошёл до записи абонента.')
            writing_new_user(data)
            return response
        elif ru_verb == 'ОТДОВАЙ':
            print('\nПытаюсь найти абонента в дб...')
            response += f'\r\n{get_user(data)}'
            print(f'Пользователь найден, ответ который верну клиенту:\r\n{response}')
            return response
        else:
            pass
                
    else:
        
        pass


def get_user(data) -> str:
    """Searching user into data base
        Args:
            data ([type]): Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    print(f'Имя пользователя в закодированном виде: {encode_name}')
    try:
        with open(f"db/{encode_name}", 'r', encoding='utf-8') as f:            
            user_data = f.read()
            print(user_data)
        return user_data
    except FileExistsError:
        return f'НИНАШОЛ РКСОК/1.0'
    

def writing_new_user(data) -> None:
    """ Writing new userfile.
        Args:
            data: Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    print(encode_name)
    with open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
        f.write(''.join(data.split('\r\n', 1)[1]))


def get_validation_body(decoded_data: str) -> bytes:
    """ Composes validation request.
        Args:
            decoded_data (str): [description]
        Returns:
            bytes: Encoded request"""
    request = f"АМОЖНА? {PROTOCOL}\r\n{decoded_data}"
    # request += "\r\n"  #TODO: Надо понять нужен ли тут доп. отступ. UPD: Вроде нет.
    return request.encode(ENCODING)


def send_validation_request(request_body: bytes) -> str:
    """ Send validation request and receive valid response.
        Args:
            request_body (bytes): Body request.
        Returns:
            str: Decoded valid response."""
    valid_conn = socket.create_connection(('0.0.0.0', 3332))  # ('vragi-vezde.to.digital', 51624)
    valid_conn.sendall(request_body)  # Отправляем запрос.
    valid_response = receive_validation_response(valid_conn)  # Ждём ответа от сервера.
    return valid_response  


def receive_validation_response(valid_conn) -> str:
        """ Receives data from socket connection and returns it as string,
            decoded using ENCODING"""
        response = b""
        # while True:  TODO: Не знаю нужен ли тут цикл while.
        data = valid_conn.recv(1024)
        # if not data: break
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

    print('Отправил ответ в клиент.')
    conn.send(valid_or_not_response.encode(ENCODING))

    print('Отключаюсь...')
    conn.shutdown(socket.SHUT_RDWR)
    
    
if __name__ == '__main__':
    run_server()