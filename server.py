import socket


server = socket.create_server(("0.0.0.0", 3333))  # Принимаем любые запросы этой машины на порт 3333.
server.listen(1)  # Длина очереди.

while True:
    print('On the top while loop')
    itertion = 0
    conn, addr = server.accept()
    print('New connection')
    while True:
        itertion += 1
        print(f'{itertion=}')
        data = conn.recv(1024)
        print(f'received {data}')
        if not data:
            print('break')
            conn.close()
            break
server.close()