# A simple worker that simulates container management using subprocesses.
import socket
import os
import subprocess
import platform

# Keep track of running "containers" in a dictionary
containers = {}

def handle_command(cmd):
    parts = cmd.split()
    system = platform.system()

    if len(parts) == 0:
        return "No command entered"

    action = parts[0]

    if action == "run":
        if len(parts) < 3:
            return "Error: Usage -> run <image> <command>"
        image = parts[1]
        command = " ".join(parts[2:])

        # Simulate container by running subprocess
        if system == "Linux":
            # Linux: use unshare if available
            try:
                pid = subprocess.Popen(
                    ["unshare", "--pid", "--fork", "--mount-proc", "bash", "-c", command]
                )
                containers[pid.pid] = command
                return f"Container started with PID {pid.pid} (Linux)"
            except FileNotFoundError:
                # fallback to normal subprocess if unshare not available
                pid = subprocess.Popen(["bash", "-c", command])
                containers[pid.pid] = command
                return f"Container simulated with PID {pid.pid} (Linux fallback)"
        else:
            # macOS / Windows / others: just simulate
            if system == "Windows":
                pid = subprocess.Popen(["cmd", "/c", command])
            else:
                pid = subprocess.Popen(["bash", "-c", command])
            containers[pid.pid] = command
            return f"Container simulated with PID {pid.pid} ({system})"

    elif action == "list":
        if not containers:
            return "No running containers"
        return "Containers:\n" + "\n".join([f"PID {pid}: {cmd}" for pid, cmd in containers.items()])

    elif action == "stop":
        if len(parts) != 2:
            return "Error: Usage -> stop <PID>"
        try:
            pid = int(parts[1])
            os.kill(pid, 9)
            containers.pop(pid, None)
            return f"Stopped container {pid}"
        except Exception as e:
            return f"Error stopping container {pid}: {e}"

    else:
        return "Unknown command"

def start_server():
    HOST = "0.0.0.0"
    PORT = 5050

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print("Worker ready.")
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024).decode()
                if not data:
                    continue
                result = handle_command(data)
                conn.send(result.encode())

if __name__ == "__main__":
    start_server()
