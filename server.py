from random import randint
import asyncio
import aiofiles
import aiofiles.os
from base64 import b64encode
from typing import Optional


PROTOCOL = "РКСОК/1.0"
ENCODING = 'UTF-8'

ru_verbs_list = {"ОТДОВАЙ ": 'GET',
                 "УДОЛИ ": 'DELETE',
                 "ЗОПИШИ ": 'WRITE'}


async def validation_server_request(message: str) -> str:
    reader, writer = await asyncio.open_connection(
        'vragi-vezde.to.digital', 51624)  #  'localhost', 3334
    request = f"АМОЖНА? {PROTOCOL}\r\n{message}"
    writer.write(request.encode())  # Отправляем в поток сообщение в бинарном виде.
    await writer.drain()  # Следит за переполнением буфера, придерживая отправку в поток.

    response = await reader.read(1024) # Получаем ответ от сервера проверки.
    print(f'\nReceived: {response.decode()!r}')
    print(f'\nClose the connection with validation server')
    writer.close()             # Закрывает поток и прилежайщий к нему сокет.
    await writer.wait_closed() # Должен идти вместе с writer.close()

    return response.decode(ENCODING)


async def parse_client_request(message: str) -> str:
    if not ' ' in message:
        return f'НИПОНЯЛ РКСОК/1.0'
    if len(message.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]) > 30:
        return f'НИПОНЯЛ РКСОК/1.0'  # Проверяем длину имени.
    if message.split('\r\n', 1)[0].rsplit(' ', 1)[1] != PROTOCOL:
        return f'НИПОНЯЛ РКСОК/1.0'  # Проверяем совпадает ли протокол.

    for ru_verb in ru_verbs_list: 
        if message.startswith(ru_verb):
            break
    else:
        return f'НИПОНЯЛ РКСОК/1.0'
    return f'{ru_verb}'


async def get_user(data: str) -> str:
    """ Searching user into data base
        Args:
            data ([type]): Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    try:
        async with aiofiles.open(f"db/{encode_name}", 'r', encoding='utf-8') as f:            
            user_data = await f.read()
        # print(f'\nЗасыпаю на 15сек...\n')  # Проверка на асинхронность.
        # await asyncio.sleep(15)
        return f'НОРМАЛДЫКС РКСОК/1.0\r\n{user_data}'
    except (FileExistsError, FileNotFoundError):
        return f'НИНАШОЛ РКСОК/1.0'


async def writing_new_user(data: str) -> str:
    """ Writing new userfile.
        Args:
            data: Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    try:
        async with aiofiles.open(f"db/{encode_name}", 'x', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return f'НОРМАЛДЫКС РКСОК/1.0'
    except FileExistsError:        
        async with aiofiles.open(f"db/{encode_name}", 'w', encoding='utf-8') as f:
            await f.write(''.join(data.split('\r\n', 1)[1]))
        return f'НОРМАЛДЫКС РКСОК/1.0'


async def deleting_user(data: str) -> str:
    """ Deleting user from data base.
        Args:
            data ([type]): Data from client response."""
    name = data.split('\r\n', 1)[0].rsplit(' ', 1)[0].split(' ', 1)[1]
    encode_name = b64encode(name.encode("UTF-8")).decode()
    # print(f'Имя пользователя в закодированном виде: {encode_name}')
    try:
        await aiofiles.os.remove(f"db/{encode_name}")
        return f'НОРМАЛДЫКС РКСОК/1.0'
    except (FileExistsError, FileNotFoundError):
        return f'НИНАШОЛ РКСОК/1.0' 


async def handle_echo(reader, writer):
    data = await reader.read(1024)  # Читает n байт из reader объекта.
    message = data.decode()  # Декодированное сообщение.
    addr = writer.get_extra_info('peername')  # Забирает из writer объекта инфо по ip и порту.
    print(f"Received: {message!r} \nfrom {addr!r}")  # Печатаем что и от кого получили.

    response = await parse_client_request(message)  # Распаршиваем запрос клиента.
    if not response.startswith('НИПОНЯЛ'):
        valid_response = await validation_server_request(message)  # Отправляем данные на валидацию серверу
        print(f'\nRequesting validation from validation server: {valid_response}\n') # проверки МОЖНА|НЕЛЬЗЯ

        if valid_response.startswith('МОЖНА'): # Распаршиваем запрос пользователя и пишем соотв. логику его запроса.
            if response == 'ЗОПИШИ ':
                response = await writing_new_user(message)
            elif response == 'ОТДОВАЙ ':
                print(f'\nЗашёл в GET с данными: {message}\n\n')
                response = await get_user(message)               
            elif response == 'УДОЛИ ':
                response = await deleting_user(message)
        else:
            # Сервер проверки запретил обрабатывать запрос, надо вернуть НИЛЬЗЯ + тело ответа сервера проверки.
            response = valid_response  # Отправляем запрет сервера валидации к клиенту.        
    
    print(f'\nОтвет для клиента: {response}')
    writer.write(response.encode('utf-8'))  # Отправляет бинарные данные как ответ в подключенный сокет.
    await writer.drain()  # Следит за переполнением буфера, придерживая отправку в поток.
    print("\nClose the connection with client")
    writer.close()  # Закрывает поток запись (обрывает соединение с сокетом).


async def main():
    server = await asyncio.start_server(
        handle_echo, '10.166.0.2', 3389)  # localhost   # Запускает сервер, вызывает handle_echo 
                                          # всякий раз когда есть новое подключение.
    addr = server.sockets[0].getsockname()  # Просто показывает какой сокет обслуживает.
    print(f'Serving on {addr}\n')
    async with server:
        await server.serve_forever()  # Позволяет объекту server принимать поключения.


if __name__ == '__main__':
    asyncio.run(main())  # Создаёт ивент луп, выполняет и управляет корутинами.
