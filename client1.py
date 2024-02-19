import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(f"Received message: {message}")
            if 'Access denied' in message:
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def start_client():
    IP = input("Enter server IP: ")
    PORT = 8888
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((IP, PORT))

    message_thread = threading.Thread(target=receive_messages, args=(client,))
    message_thread.start()

    while True:
        user_input = input("Enter your message: ")
        client.send(user_input.encode('utf-8'))

if __name__ == "__main__":
    start_client()
