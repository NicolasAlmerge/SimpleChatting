import threading
import socket
from sty import fg, ef

HOST = "127.0.0.1"
PORT = 65432

"""
try:
    with open(".chat_config") as f:
        nickname = f.read()
except FileNotFoundError:
    nickname = ""

if not nickname.strip():
    while True:
        nickname = input("Choose a nickname: ")
        if nickname.strip():
            break
        print("Error: nickname cannot be empty!")
    with open(".chat_config", "w") as f:
        f.write(nickname)
"""

nickname = input("Enter nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
stop_thread = False


def receive():
    """Main loop."""
    global stop_thread
    while True:
        try:
            message = client.recv(1024).decode("utf-8")
            if message == "/delete":
                print(fg.red + ef.bold + "\nGroup deleted!" + ef.rs + fg.rs + "\n")
                stop_thread = True
                client.close()
                break
            if message == "/kick":
                print(fg.red + ef.bold + "\nYou were kicked!" + ef.rs + fg.rs + "\n")
                stop_thread = True
                client.close()
                break
            if message == "/ban":
                print(fg.red + ef.bold + "\nYou were banned!" + ef.rs + fg.rs + "\n")
                stop_thread = True
                client.close()
                break
            if message == "/quit":
                print(fg.red + ef.bold + "\nYou quit the group!" + ef.rs + fg.rs + "\n")
                stop_thread = True
                client.close()
                break
            if message == "/nick":
                client.send(nickname.encode("utf-8"))
            elif message.endswith("\n"):
                print(message, end="")
            else:
                print(message)
        except Exception:
            # print("An error occurred!")
            client.close()
            break


def write():
    """Writes message author and content."""
    while not stop_thread:
        try:
            input_msg = input().strip()
            if not input_msg:
                continue
            client.send(input_msg.encode("utf-8"))
        except:
            client.close()
            break


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
