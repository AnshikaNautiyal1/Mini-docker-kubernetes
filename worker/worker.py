# # A simple worker that simulates container management using subprocesses.
# import socket
# import os
# import subprocess
# import platform

# # Keep track of running "containers" in a dictionary
# containers = {}

# def handle_command(cmd):
#     parts = cmd.split()
#     system = platform.system()

#     if len(parts) == 0:
#         return "No command entered"

#     action = parts[0]

#     if action == "run":
#         if len(parts) < 3:
#             return "Error: Usage -> run <image> <command>"
#         image = parts[1]
#         command = " ".join(parts[2:])

#         # Simulate container by running subprocess
#         if system == "Linux":
#             # Linux: use unshare if available
#             try:
#                 pid = subprocess.Popen(
#                     ["unshare", "--pid", "--fork", "--mount-proc", "bash", "-c", command]
#                 )
#                 containers[pid.pid] = command
#                 return f"Container started with PID {pid.pid} (Linux)"
#             except FileNotFoundError:
#                 # fallback to normal subprocess if unshare not available
#                 pid = subprocess.Popen(["bash", "-c", command])
#                 containers[pid.pid] = command
#                 return f"Container simulated with PID {pid.pid} (Linux fallback)"
#         else:
#             # macOS / Windows / others: just simulate
#             if system == "Windows":
#                 pid = subprocess.Popen(["cmd", "/c", command])
#             else:
#                 pid = subprocess.Popen(["bash", "-c", command])
#             containers[pid.pid] = command
#             return f"Container simulated with PID {pid.pid} ({system})"

#     elif action == "list":
#         if not containers:
#             return "No running containers"
#         return "Containers:\n" + "\n".join([f"PID {pid}: {cmd}" for pid, cmd in containers.items()])

#     elif action == "stop":
#         if len(parts) != 2:
#             return "Error: Usage -> stop <PID>"
#         try:
#             pid = int(parts[1])
#             os.kill(pid, 9)
#             containers.pop(pid, None)
#             return f"Stopped container {pid}"
#         except Exception as e:
#             return f"Error stopping container {pid}: {e}"

#     else:
#         return "Unknown command"

# def start_server():
#     HOST = "0.0.0.0"
#     PORT = 5050

#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.bind((HOST, PORT))
#         s.listen(5)
#         print("Worker ready.")
#         while True:
#             conn, addr = s.accept()
#             with conn:
#                 data = conn.recv(1024).decode()
#                 if not data:
#                     continue
#                 result = handle_command(data)
#                 conn.send(result.encode())

# if __name__ == "__main__":
#     start_server()



# worker.py
import socket, json, subprocess, threading, sys, time, psutil

LOG_FILE = "worker_log.json"

def log(event, detail):
    entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "detail": detail}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def monitor_process(pid, cid):
    try:
        p = psutil.Process(pid)
        while p.is_running():
            cpu = p.cpu_percent(interval=1)
            mem = p.memory_info().rss / (1024 * 1024)
            print(f"[Monitor] Container={cid} PID={pid} CPU={cpu}% MEM={mem:.1f}MB")
            time.sleep(2)
    except psutil.NoSuchProcess:
        print(f"[Monitor] Container {cid} ended.")

def handle_run(cid, cmd):
    proc = subprocess.Popen(cmd, shell=True)
    pid = proc.pid
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    log("container_start", {"cid": cid, "pid": pid, "command": cmd})
    threading.Thread(target=monitor_process, args=(pid, cid), daemon=True).start()
    return {"status": "started", "pid": pid, "started_at": started_at}

def start_worker(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", port))
    s.listen(5)
    print(f"=== Worker listening on port {port} ===")
    while True:
        conn, _ = s.accept()
        data = json.loads(conn.recv(4096).decode())
        if data["type"] == "run_container":
            result = handle_run(data["container_id"], data["command"])
            conn.send(json.dumps(result).encode())
        conn.close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    start_worker(port)
