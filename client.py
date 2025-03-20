import socket
import threading
import sys

# Local variables to track our nickname and channel.
local_nickname = ""
local_channel = "Global"

# Global Event that will be set when the welcome message is received.
welcome_received = threading.Event()

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode("utf-8")
            # if stop receiving messages, disconnected
            if not message:
                print("Disconnected from server.")
                break
            print(message)
            if message.startswith("Welcome"):
                welcome_received.set()
        except Exception as e:
            if hasattr(e, 'errno') and e.errno == 10053:
                print("Disconnected from server..")
                break
            print("Error receiving message:", e)
            break

def show_commands():
    print("\nAvailable commands:")
    print("/nick <name>       -> Set your nickname")
    print("/channel <channel> -> Join or create a channel")
    print("/pm <nick <msg>    -> Send a private message")
    print("/help              -> Show available commands")
    print("/quit              -> Disconnect\n")

def clear_current_line():
    #Uses ANSI escape codes to clear the current input line.
    #\033[F moves the cursor up one line, \033[K clears the line.
    print("\033[F\033[K", end="")

def main():
    global local_nickname, local_channel

    server_ip = input("Enter server IP address: ").strip()
    local_nickname = input("Enter your nickname: ").strip()
    if not local_nickname:
        local_nickname = "Default User"
    
    port = 3000
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, port))
    except Exception as e:
        print("Connection error: ", e)
        sys.exit(1)
    
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    # Wait until we receive the welcome message
    welcome_received.wait()

    # Set users nickname
    client_socket.send(local_nickname.encode("utf-8"))

    show_commands()


    try:
        while True:
            msg = input()
            if msg.strip() == "":
                continue
            if msg.startswith("/help"):
                show_commands()
                continue
            if msg.startswith("/nick "):
                new_nick = msg.split(" ", 1)[1].strip()
                local_nickname = new_nick
            if msg.startswith("/channel "):
                new_channel = msg.split(" ", 1)[1].strip()
                local_channel = new_channel
            if msg.startswith("/quit"):
                break

            # For regular messages sent to the server chat, clear the input and show it formatted.
            if not msg.startswith("/"):
                clear_current_line()  # Clears the raw input line.
                formatted_message = f"[{local_channel}] {local_nickname}: {msg}"
                print(formatted_message)
            
            # Send the message to the server.
            client_socket.send(msg.encode("utf-8"))
    except KeyboardInterrupt:
        client_socket.send("/quit".encode("utf-8"))
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()