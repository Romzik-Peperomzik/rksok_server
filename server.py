from random import randint
import asyncio
import aiofiles
import aiofiles.os
from base64 import b64encode


PROTOCOL = "РКСОК/1.0"
ENCODING = 'UTF-8'


async def validation_server_request(message: str):
    reader, writer = await asyncio.open_connection(
        'localhost', 3334)

    request = f"АМОЖНА? {PROTOCOL}\r\n{message}"
    writer.write(request.encode())  # Отправляем в поток сообщение в бинарном виде.
    await writer.drain()  # Следит за переполнением буфера, придерживая отправку в поток.

    response = await reader.read(1024) # Получаем ответ от сервера проверки.
    print(f'\nReceived: {response.decode()!r}')
    print('Close the connection')
    writer.close()             # Закрывает поток и прилежайщий к нему сокет.
    await writer.wait_closed() # Должен идти вместе с writer.close()

    return response


async def handle_echo(reader, writer):
    data = await reader.read(1024)  # Читает n байт из reader объекта.
    message = data.decode()  # Декодированное сообщение.
    addr = writer.get_extra_info('peername')  # Забирает из writer объекта инфо по ip и порту.
    print(f"Received {message!r} from {addr!r}")  # Печатаем что и от кого получили.
    print(f"Send: {message!r}")  # Печатаем ответ для адреса выше.

    valid_response = await validation_server_request(message)
    print(f'\nResponse from validation server: {valid_response.decode(ENCODING)}\n')

    writer.write(valid_response)  # Отправляет бинарные данные как ответ в подключенный сокет.
    await writer.drain()  # Следит за переполнением буфера, придерживая отправку в поток.
    print("Close the connection")
    writer.close()  # Закрывает поток запись (обрывает соединение с сокетом).


async def main():
    server = await asyncio.start_server(
        handle_echo, 'localhost', 3333)   # Запускает сервер, вызывает handle_echo 
                                          # всякий раз когда есть новое подключение.
    addr = server.sockets[0].getsockname()  # Просто показывает какой сокет обслуживает.
    print(f'Serving on {addr}\n')
    async with server:
        await server.serve_forever()  # Позволяет объекту server принимать поключения.


if __name__ == '__main__':
    asyncio.run(main())  # Создаёт ивент луп, выполняет и управляет корутинами.