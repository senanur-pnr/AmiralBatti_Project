import socket
import threading

HOST = "0.0.0.0"
PORT = 6060

clients = []

def handle_client(conn, addr):
    print(f"Bağlandı: {addr}")

    player_index = len(clients)
    clients.append(conn)
    conn.send(f"PLAYER:{player_index}".encode())

    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            #diğer clienta gönder
            for client in clients:
                if client != conn:
                    client.send(data.encode())
        except:
            break
    print(f"Bağlantı kesildi: {addr}")
    if conn in clients:
        clients.remove(conn)
    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(2)

    print("Server çalışıyor...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()