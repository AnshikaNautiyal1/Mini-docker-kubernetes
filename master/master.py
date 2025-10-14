# import socket, json

# def send_command(node_ip, command):
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.connect((node_ip, 5050))
#     s.send(command.encode())
#     data = s.recv(1024).decode()
#     print("Response:", data)
#     s.close()

# if __name__ == "__main__":
#     while True:
#         cmd = input("EduDistOS> ")
#         if cmd.startswith("run") or cmd.startswith("list") or cmd.startswith("stop"):
#             send_command("127.0.0.1", cmd)
#         else:
#             print("Unknown command")

import socket, json, os

# List of available worker nodes (IP, PORT)
workers = [
    ("127.0.0.1", 5000),
    # You can add more workers on different ports if you run more worker.py instances
    # ("127.0.0.1", 5001),
]

# Keep track of which worker to assign next (Round Robin index)
current_worker = 0

def send_command(node_ip, port, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((node_ip, port))
    s.send(command.encode())
    data = s.recv(1024).decode()
    print("Response:", data)
    s.close()

def schedule_worker():
    global current_worker
    node = workers[current_worker]
    current_worker = (current_worker + 1) % len(workers)
    return node

if __name__ == "__main__":
    print("EduDistOS Scheduler Active. Available workers:", len(workers))
    while True:
        cmd = input("EduDistOS> ")
        if cmd.startswith("run"):
            node_ip, port = schedule_worker()
            print(f"[Scheduler] Assigning new container to {node_ip}:{port}")
            send_command(node_ip, port, cmd)
        elif cmd.startswith("list") or cmd.startswith("stop"):
            # Broadcast to all workers for list/stop commands
            for node_ip, port in workers:
                send_command(node_ip, port, cmd)
        else:
            print("Available commands: run <image> <cmd>, list, stop <pid>")