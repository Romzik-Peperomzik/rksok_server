import socket
from enum import Enum
from base64 import b64encode
from os import remove
import time

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
        return f'НИПОНЯЛ РКСОК/1.0'
    if len(data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) > 30:
        return f'НИПОНЯЛ РКСОК/1.0'

    validation_request = get_validation_body(data)  # Формируем запрос для сервера проверки.
    validation_response = send_validation_request(validation_request)  # Идём узнавать у сервера проверки.
    print('\nОтвет от сервера валидации получен.')
    
    if validation_response.startswith('МОЖНА'):
        if ru_verb == 'ЗОПИШИ':
            print('\nПытаюсь записать абонента в дб...')            
            return writing_new_user(data)
        elif ru_verb == 'ОТДОВАЙ':
            print('\nПытаюсь найти абонента в дб...')            
            return get_user(data)
        else:
            print('\nПытаюсь удалить абонента из дб...')
            return deleting_user(data)
                
    else:        
        print(validation_response)
        return validation_response


def deleting_user(data) -> None:
    """Deleting user from data base.
        Args:
            data ([type]): Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    print(f'Имя пользователя в закодированном виде: {encode_name}')
    try:
        print('Пытаюсь удалить пользователя.')
        remove(f"db/{encode_name}")
        return f'НОРМАЛДЫКС РКСОК/1.0'
    except FileExistsError:
        return f'НИНАШОЛ РКСОК/1.0'


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
        return f'НОРМАЛДЫКС РКСОК/1.0\r\n{user_data}'
    except FileExistsError:
        return f'НИНАШОЛ РКСОК/1.0'
    

def writing_new_user(data) -> None:
    """ Writing new userfile.
        Args:
            data: Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    print(encode_name)
    try:
        with open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
            f.write(''.join(data.split('\r\n', 1)[1]))
        return f'НОРМАЛДЫКС РКСОК/1.0'
    except FileExistsError:
        print('Кажется такой файл уже существует.')


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
    try:
        while True:
            print('Waiting for connection...')
            conn, addr = server.accept()  # Объект для работы с клиентским сокетом. Адрес клиента.

            print('Got new connection')
            data = f'{conn.recv(1024).decode(ENCODING)}'
            response_to_client = parse_response(data)
            # time.sleep(15)
            print('Отправил ответ в клиент.')
            conn.send(response_to_client.encode(ENCODING))

            print('Отключаюсь...')
            conn.shutdown(socket.SHUT_RDWR)
    except KeyboardInterrupt:
        print('\nТы отключил сервер.')
        server.close()
    
    
if __name__ == '__main__':
    run_server()