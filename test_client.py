import asyncio
import aiofiles
import aiofiles.os
from base64 import b64encode


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        'localhost', 3333)  # Устанавливает соединение с сетью и возвращает пару инстансов для
                            # записи и чтения потока.
    print(f'Send: {message!r}')  # Что будем отправлять.
    writer.write(message.encode())  # Отправляем в поток сообщение в бинарном виде.
    await writer.drain()  # Следит за переполнением буфера, придерживая отправку в поток.

    data = await reader.read(1024)  # Получаем ответ от сервера из потока чтения.
    print(f'\nReceived: {data.decode()!r}')

    print('Close the connection')
    writer.close()             # Закрывает поток и прилежайщий к нему сокет.
    await writer.wait_closed() # Должен идти вместе с writer.close()

asyncio.run(tcp_echo_client('Hello World!'))  # Создаёт ивент луп, выполняет и управляет корутинами.
