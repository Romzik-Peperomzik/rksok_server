from random import randint
import asyncio
import aiofiles
import aiofiles.os
from base64 import b64encode


ENCODING = 'UTF-8'

allow_or_not_list = ['МОЖНА РКСОК/1.0', 'НИЛЬЗЯ РКСОК/1.0\r\nУже едем']


async def handle_echo(reader, writer):
    data = await reader.read(1024)  # Читает n байт из reader объекта.
    message = data.decode()
    addr = writer.get_extra_info('peername')  # Забирает из writer объекта инфо по ip и порту.
    print(f"\nReceived: \n{message!r}\nfrom {addr!r}")  # Печатаем что и от кого получили.
    print(f'Ok, making response...')
    print(f'\n{allow_or_not_list[0]}', end='\n')
    
    writer.write(allow_or_not_list[0].encode('utf-8'))  # Отправляет бинарные данные как ответ в подключенный сокет.
    await writer.drain()  # Следит за переполнением буфера, придерживая отправку в поток.
    print("Close the connection")
    writer.close()  # Закрывает поток запись (обрывает соединение с сокетом).

async def main():
    server = await asyncio.start_server(
        handle_echo, 'localhost', 3334)   # Запускает сервер, вызывает handle_echo 
                                          # всякий раз когда есть новое подключение.
    addr = server.sockets[0].getsockname()  # Просто показывает какой сокет обслуживает.
    print('Validation server waiting for connection')
    print(f'Serving on {addr}')
    async with server:
        await server.serve_forever()  # Позволяет объекту server принимать поключения.

asyncio.run(main())  # Создаёт ивент луп, выполняет и управляет корутинами.