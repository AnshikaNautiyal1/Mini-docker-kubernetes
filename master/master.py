import socket, json

def send_command(node_ip, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((node_ip, 5050))
    s.send(command.encode())
    data = s.recv(1024).decode()
    print("Response:", data)
    s.close()

if __name__ == "__main__":
    while True:
        cmd = input("EduDistOS> ")
        if cmd.startswith("run") or cmd.startswith("list") or cmd.startswith("stop"):
            send_command("127.0.0.1", cmd)
        else:
            print("Unknown command")

