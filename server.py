import socket
import asyncio
import aiofiles
import aiofiles.os
from base64 import b64encode
from os import remove

PROTOCOL = "РКСОК/1.0"
ENCODING = "UTF-8" 


class CanNotParseResponseError(Exception):
    """ Error that occurs when we can not parse some strange
        response from RKSOK client."""
    pass


ru_verbs_list = {"ОТДОВАЙ": 'GET',
                 "УДОЛИ": 'DELETE',
                 "ЗОПИШИ": 'WRITE'}


class SocketException(Exception):
    pass


class Server():
    def __init__(self):
        super(Server, self).__init__()
        self.users = []
        self.socket = socket.create_server(("0.0.0.0", 3333))  # socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.validation_server_socket = socket.create_connection(('0.0.0.0', 3332))
        self.is_working = False
        self.main_loop = asyncio.new_event_loop()

    def set_up(self):
        # self.socket.bind('localhost', 3333)
        self.socket.listen(5)
        self.socket.setblocking(False)
        print("Server is listening")

    def start(self):
        self.is_working = True
        self.main_loop.run_until_complete(self.main())

    async def main(self):
        await self.main_loop.create_task(self.accept_sockets())

    async def accept_sockets(self):
        while True:
            user_socket, address = await self.main_loop.sock_accept(self.socket)
            print(f"User <{address[0]}> connected!")

            self.users.append(user_socket)
            self.main_loop.create_task(self.listen_socket(user_socket))

    async def listen_socket(self, listened_socket=None):
        while True:
            if listened_socket:
                print(listened_socket, end='\n')         
                data = await self._recv_message(listened_socket)  # Данные от клиента(б).
                parsed_data, verb = self.parse_response(data)  # Валиден ли запрос клиента.

                if parsed_data.startswith('НИПОНЯЛ'):  # Невалидный запрос, отвечаем клиенту.
                    await self.send_data(parsed_data)
                    listened_socket.close()
                                
                valid_body = self.get_validation_body(parsed_data)  # Формируем запрос на валидацию.
                print(f'{valid_body.decode(ENCODING)}\n')
                valid_response = await self.send_validation_request(self.validation_server_socket, valid_body)
                print(valid_response)
                if valid_response.startswith('МОЖНА'):
                    if verb == 'ЗОПИШИ':
                        print('\nПытаюсь записать абонента в дб...')
                        response = await self.writing_new_user(parsed_data)
                        await self.send_data(response)
                        # listened_socket.close()
                        break

                    elif verb == 'ОТДОВАЙ':
                        print('\nПытаюсь найти абонента в дб...')   
                        print(parsed_data)
                        response = await self.get_user(parsed_data)
                        await self.send_data(response)
                        break

                    else:
                        print('\nПытаюсь удалить абонента из дб...')
                        response = await self.deleting_user(parsed_data)
                        await self.send_data(response)
                        break

    async def _recv_message(self, listened_socket: socket.socket) -> str:
        message = b''
        message += await self.main_loop.sock_recv(listened_socket, 1024)
        if message is None:
            return None        
        return message.decode(ENCODING)
    
    async def send_data(self, raw_data):
        for user_socket in self.users:
            try:
                await self.main_loop.sock_sendall(user_socket, raw_data)
                user_socket.close()
            except (KeyError, UnicodeEncodeError, ConnectionError, ValueError) as exc:
                raise SocketException(exc)

    async def send_validation_request(self, valid_sock, request_body: bytes) -> str:
        try:
            await self.main_loop.sock_sendall(valid_sock, request_body)
            valid_response =  await self._recv_message(valid_sock)
            return valid_response
        except (KeyError, UnicodeEncodeError, ConnectionError, ValueError) as exc:
                raise SocketException(exc)

    def parse_response(self, data: str) -> tuple:
        """Processing client response
            Args:
                raw_response (str): Запрос.
            Raises:
                CanNotParseResponseError: Ошибка если команду запроса неудалось обработать.
            Returns:
                str: [description]"""    
        for ru_verb in ru_verbs_list: 
            if data.startswith(ru_verb):
                break
        else:
            return f'НИПОНЯЛ РКСОК/1.0'
        if len(data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) > 30:
            return f'НИПОНЯЛ РКСОК/1.0'
        return data, ru_verb

    def get_validation_body(self, decoded_data: str) -> bytes:
        """ Composes validation request.
            Args:
                decoded_data (str): [description]
            Returns:
                bytes: Encoded request"""
        request = f"АМОЖНА? {PROTOCOL}\r\n{decoded_data}"
        return request.encode(ENCODING)

    async def get_user(self, data) -> str:
        """ Searching user into data base
            Args:
                data ([type]): Data from client response."""
        name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
        encode_name = b64encode(name.encode("UTF-8")).decode()
        print(f'Имя пользователя в закодированном виде: {encode_name}')
        try:
            async with aiofiles.open(f"db/{encode_name}", 'r', encoding='utf-8') as f:            
                user_data = await f.read()
                print(user_data)

            return f'НОРМАЛДЫКС РКСОК/1.0\r\n{user_data}'.encode(ENCODING)

        except (FileExistsError, FileNotFoundError):
            return f'НИНАШОЛ РКСОК/1.0'.encode(ENCODING)

    async def writing_new_user(self, data) -> None:
        """ Writing new userfile.
            Args:
                data: Data from client response."""
        name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
        encode_name = b64encode(name.encode("UTF-8")).decode()
        print(encode_name)
        try:
            async with aiofiles.open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
                await f.write(''.join(data.split('\r\n', 1)[1]))

            return f'НОРМАЛДЫКС РКСОК/1.0'.encode(ENCODING)

        except FileExistsError:
            print('Кажется такой файл уже существует.')

    async def deleting_user(self, data) -> None:
        """ Deleting user from data base.
            Args:
                data ([type]): Data from client response."""
        name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
        encode_name = b64encode(name.encode("UTF-8")).decode()
        print(f'Имя пользователя в закодированном виде: {encode_name}')
        try:
            print('Пытаюсь удалить пользователя.')
            await aiofiles.os.remove(f"db/{encode_name}")

            return f'НОРМАЛДЫКС РКСОК/1.0'.encode(ENCODING)

        except FileExistsError:
            return f'НИНАШОЛ РКСОК/1.0'.encode(ENCODING)       


if __name__ == '__main__':
    server = Server()
    server.set_up()
    server.start()