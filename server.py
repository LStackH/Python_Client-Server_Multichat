import socket
import threading

#Keeps track of clients connected
clients = {}
#Keeps track of channels and the clients connected to those channels
channels = {"Global": []}

#send message all clients in specified channel
def broadcast(message, channel, sender_sock=None):
    for client in channels.get(channel, []):
        #If client is the sender, dont send the message
        if client != sender_sock:
            try:
                client.send(message.encode("utf-8"))
            except Exception as e:
                #if error in sending, removes client socket so that reconnection can be tried
                print("Error sending message to a client:", e)
                client.close()
                remove_client(client)

# Function to remove client from all channels and client list
def remove_client(client):
    for members in channels.values():
        if client in members:
            members.remove(client)
    if client in clients:
        del clients[client]

#Handles communication with connected client & processes commands
def client_handler(client_socket, address):
    client_socket.send("Welcome to chat server!".encode("utf-8"))

    # Wait for the first message which is the chosen nickname.
    try:
        initial_nick = client_socket.recv(1024).decode("utf-8").strip()
    except Exception as e:
        print(f"Error receiving initial nickname from {address}: {e}")
        client_socket.close()
        return
    if not initial_nick:
        initial_nick = "Default User"

    current_channel = "Global"
    channels[current_channel].append(client_socket)
    clients[client_socket] = {"nickname": initial_nick, "channel": current_channel}
    # Notify the client that the nickname is set
    client_socket.send(f"Your nickname is set to {initial_nick}".encode("utf-8"))
    print(f"Client {address} joined as {initial_nick} in channel {current_channel}.")

    try:
        while True:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                break

            if message.startswith("/nick "):
                # Command for changing nickname
                new_nick = message.split(" ", 1)[1].strip()
                old_nick = clients[client_socket]["nickname"]
                clients[client_socket]["nickname"] = new_nick
                client_socket.send(f"Nickname changed to {new_nick}".encode("utf-8"))
                broadcast(f"[Server]: {old_nick} has changed name to {new_nick}", current_channel, client_socket)

            elif message.startswith("/channel "):
                # Command to join or create a new channel.
                new_channel = message.split(" ", 1)[1].strip()
                old_channel = clients[client_socket]["channel"]
                # Remove the client from the old channel.
                if client_socket in channels[old_channel]:
                    channels[old_channel].remove(client_socket)
                # Create the channel if it doesn't exist.
                if new_channel not in channels:
                    channels[new_channel] = []
                channels[new_channel].append(client_socket)
                clients[client_socket]["channel"] = new_channel
                current_channel = new_channel
                client_socket.send(f"Joined channel {new_channel}".encode('utf-8'))
            
            elif message.startswith("/pm "):
                # Command for private messaging: /pm <nickname> <message>
                parts = message.split(" ", 2)
                if len(parts) < 3:
                    client_socket.send("Usage: /pm <nickname> <message>".encode('utf-8'))
                else:
                    target_nick = parts[1].strip()
                    pm_message = parts[2].strip()
                    sender_nick = clients[client_socket]["nickname"]
                    # Find the target client's socket based on their nickname.
                    target_socket = None
                    for sock, info in clients.items():
                        if info["nickname"] == target_nick:
                            target_socket = sock
                            break
                    if target_socket:
                        target_socket.send(f"[PM from {sender_nick}]: {pm_message}".encode('utf-8'))
                        client_socket.send(f"[PM to {target_nick}]: {pm_message}".encode('utf-8'))
                    else:
                        client_socket.send(f"User {target_nick} not found.".encode('utf-8'))

            elif message.startswith("/quit"):
                # Command to disconnect.
                client_socket.send("Disconnecting...".encode('utf-8'))
                break

            else:
                # Regular message: broadcast it to all clients in the current channel.
                sender_nick = clients[client_socket]["nickname"]
                full_message = f"[{current_channel}] {sender_nick}: {message}"
                broadcast(full_message, current_channel, client_socket)

    except Exception as e:
        print(f"Error with client {address}: {e}")
    finally:
        remove_client(client_socket)
        client_socket.close()
        print(f"Client {address} disconnected.")

#main server loop
def main():
    host = "0.0.0.0"
    port = 3000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET (IPv4) and SOCK_STREAM (TCP)
    server_socket.bind((host, port))
    server_socket.listen(5)
    server_socket.settimeout(1)
    print(f"Chat server started on {host}:{port}")

    try:
        while True:
            try:
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")
                threading.Thread(target=client_handler, args=(client_socket, address), daemon=True).start()
            except socket.timeout:
                # Timeout happened, loop again so we can check for KeyboardInterrupt.
                continue
    except KeyboardInterrupt:
        print("Server shutting down due to KeyboardInterrupt")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
