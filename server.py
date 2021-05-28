import socket
from enum import Enum

retranslated_verb = {"ОТДОВАЙ": 'GET',
                    "УДОЛИ": 'DELETE',
                    "ЗОПИШИ": 'WRITE'}
    

server = socket.create_server(("0.0.0.0", 3333))  # Принимаем любые запросы этой машины на порт 3333.
server.listen(1)  # Длина очереди.

while True:
    print('Waiting for connection...')
    conn, addr = server.accept()  # Объект для работы с клиентским сокетом. Адрес клиента.
    print('Got new connection')
    while True:
        data = f'{conn.recv(1024).decode("UTF-8")}'
        for verb in retranslated_verb:
            if data.startswith(verb):
                mode_to_verb = retranslated_verb[verb]
                break
        print(data)
        break
    response = f'НОРМАЛДЫКС РКСОК/1.0\r\n812334554\r\n{mode_to_verb}\r\n\r\n'
    conn.send(response.encode("UTF-8"))
    conn.shutdown(socket.SHUT_RDWR)
# server.close()