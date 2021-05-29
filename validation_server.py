import socket

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
            print('Connection closedd')
            conn.close()
            break