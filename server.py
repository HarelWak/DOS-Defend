import socket
import threading
import sqlite3
import time

# SQLite database initialization
conn = sqlite3.connect('client_database.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS clients (address TEXT, attempts INTEGER, last_attempt INTEGER)')
conn.commit()

clients = []

def handle_client(client_socket, client_address):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"Received message from {client_address}: {message}")
            broadcast(message, client_socket)
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
            break

    remove_client(client_socket)
    client_socket.close()

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error broadcasting message to a client: {e}")

def remove_client(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)

def update_database(client_address):
    cursor.execute('SELECT * FROM clients WHERE address=?', (client_address,))
    record = cursor.fetchone()

    if record:
        attempts = record[1] + 1
        current_time = int(time.time())
        cursor.execute('UPDATE clients SET attempts=?, last_attempt=? WHERE address=?', (attempts, current_time, client_address))
    else:
        cursor.execute('INSERT INTO clients VALUES (?, 1, ?)', (client_address, int(time.time())))

    conn.commit()

def check_access(client_address):
    current_time = int(time.time())
    cursor.execute('SELECT * FROM clients WHERE address=?', (client_address,))
    record = cursor.fetchone()

    if record and record[1] >= 5 and current_time - record[2] < 60: #needs to be 5 connections at least in the last minute to consider dos attack in the system
        return False
    elif record and current_time - record[2] >= 60:
        # reset attempts and update timestamp after 1 minute cooldown
        cursor.execute('UPDATE clients SET attempts=?, last_attempt=? WHERE address=?', (0, current_time, client_address))
        conn.commit()
        return True
    else:
        return True

def send_denial_message(client_socket, denial_message):
    try:
        client_socket.send(denial_message.encode('utf-8'))
    except Exception as e:
        print(f"Error sending denial message to client: {e}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    IP = socket.gethostbyname(socket.gethostname())
    print("The server IP is:", IP)
    PORT = 8888
    server.bind((IP, PORT))
    server.listen(5)

    print("Server listening on port 8888...")

    while True:
        client_socket, addr = server.accept()
        client_address = addr[0]

        if check_access(client_address):
            print(f"Accepted connection from {addr}")
            clients.append(client_socket)
            client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_handler.start()
        else:
            print(f"Access denied for {client_address}. Too many attempts in the last minute.")
            send_denial_message(client_socket, "Access denied. Too many attempts in the last minute.")

        update_database(client_address)

if __name__ == "__main__":
    start_server()
