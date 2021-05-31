import socket
from random import randint


allow_or_not_list = ['МОЖНА РКСОК/1.0', 'НИЛЬЗЯ РКСОК/1.0']

server = socket.create_server(('0.0.0.0', 3332))
server.listen(1)


while True:
    print('Validation server waiting for connection')
    iteration = 0
    conn, addr = server.accept()
    print('New validation request')
    while True:
        iteration += 1
        print(f'{iteration}')
        data = conn.recv(1024)
        print(f'Received response: \n{data.decode("UTF-8")}')
        if not data:
            print('Connection closed')
            conn.close()
            break
        print(f'Ok, making response...')
        conn.sendall(allow_or_not_list[0].encode("UTF-8")) # randint(0, 1)
        print(f'Response send.')