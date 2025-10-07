import socket, os, subprocess

def handle_command(cmd):
    if cmd.startswith("run"):
        parts = cmd.split()
        image = parts[1]
        command = " ".join(parts[2:])
        pid = subprocess.Popen(["unshare", "--pid", "--fork", "--mount-proc", "bash", "-c", command])
        return f"Container started with PID {pid.pid}"
    elif cmd == "list":
        return "Containers: <simulate list>"
    elif cmd.startswith("stop"):
        pid = cmd.split()[1]
        os.system(f"kill {pid}")
        return f"Stopped container {pid}"
    else:
        return "Unknown command"

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 5000))
    s.listen(5)
    print("Worker ready.")
    while True:
        conn, addr = s.accept()
        data = conn.recv(1024).decode()
        result = handle_command(data)
        conn.send(result.encode())
        conn.close()

if __name__ == "__main__":
    start_server()
