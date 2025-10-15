# # import socket, json

# # def send_command(node_ip, command):
# #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# #     s.connect((node_ip, 5050))
# #     s.send(command.encode())
# #     data = s.recv(1024).decode()
# #     print("Response:", data)
# #     s.close()

# # if __name__ == "__main__":
# #     while True:
# #         cmd = input("EduDistOS> ")
# #         if cmd.startswith("run") or cmd.startswith("list") or cmd.startswith("stop"):
# #             send_command("127.0.0.1", cmd)
# #         else:
# #             print("Unknown command")



# import socket, json, os

# # List of available worker nodes (IP, PORT)
# workers = [
#     ("127.0.0.1", 5000),
#     # You can add more workers on different ports if you run more worker.py instances
#     # ("127.0.0.1", 5001),
# ]

# # Keep track of which worker to assign next (Round Robin index)
# current_worker = 0

# def send_command(node_ip, port, command):
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.connect((node_ip, port))
#     s.send(command.encode())
#     data = s.recv(1024).decode()
#     print("Response:", data)
#     s.close()

# def schedule_worker():
#     global current_worker
#     node = workers[current_worker]
#     current_worker = (current_worker + 1) % len(workers)
#     return node

# if __name__ == "__main__":
#     print("EduDistOS Scheduler Active. Available workers:", len(workers))
#     while True:
#         cmd = input("EduDistOS> ")
#         if cmd.startswith("run"):
#             node_ip, port = schedule_worker()
#             print(f"[Scheduler] Assigning new container to {node_ip}:{port}")
#             send_command(node_ip, port, cmd)
#         elif cmd.startswith("list") or cmd.startswith("stop"):
#             # Broadcast to all workers for list/stop commands
#             for node_ip, port in workers:
#                 send_command(node_ip, port, cmd)
#         else:
#             print("Available commands: run <image> <cmd>, list, stop <pid>")



# master.py
import socket, json, time, uuid, os

WORKERS = [("127.0.0.1", 5001), ("127.0.0.1", 5002)]
current_worker = 0
CONTAINERS_FILE = "containers.json"

# Load and save metadata file
def load_containers():
    if os.path.exists(CONTAINERS_FILE):
        with open(CONTAINERS_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_containers(data):
    with open(CONTAINERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Register a new container entry
def register_container(record):
    data = load_containers()
    data.append(record)
    save_containers(data)

def update_container(cid, updates):
    data = load_containers()
    for r in data:
        if r.get("container_id") == cid:
            r.update(updates)
            break
    save_containers(data)

# Send tasks to workers via TCP
def send_to_worker(worker, payload):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(worker)
    s.send(json.dumps(payload).encode())
    resp = s.recv(4096).decode()
    s.close()
    try:
        return json.loads(resp)
    except:
        return {"status": "error"}

# Schedule container using Round Robin
def schedule(command_str):
    global current_worker
    worker = WORKERS[current_worker]
    current_worker = (current_worker + 1) % len(WORKERS)

    cid = uuid.uuid4().hex[:12]
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Basic metadata (you can expand this later)
    record = {
        "container_id": cid,
        "container_name": f"container-{cid[:6]}",
        "command": command_str,
        "worker": f"{worker[0]}:{worker[1]}",
        "created_at": timestamp,
        "state": {"status": "assigned"},
        "process_details": {},
        "resource_config": {"limits": {"cpu": "500m", "memory": "256Mi"}},
    }
    register_container(record)

    payload = {"type": "run_container", "container_id": cid, "command": command_str}
    print(f"[MASTER] Sending '{command_str}' → Worker {worker[1]}")

    ack = send_to_worker(worker, payload)
    if ack.get("status") == "started":
        update_container(cid, {
            "state": {"status": "running", "started_at": ack.get("started_at")},
            "process_details": {"pid": ack.get("pid")},
        })
        print(f"[MASTER] Container {cid} started on Worker {worker[1]}")
    else:
        update_container(cid, {"state": {"status": "error"}})

# Display all container records
def list_containers():
    data = load_containers()
    if not data:
        print("No containers recorded.")
        return
    for r in data:
        print(f"{r['container_id']} | {r['worker']} | {r['command']} | {r['state']['status']}")

if __name__ == "__main__":
    print("=== EduDistOS Master Node (Round Robin Scheduler) ===\n")
    while True:
        cmd = input("EduDistOS> ").strip()
        if cmd.lower() in ("exit", "quit"):
            break
        elif cmd.startswith("run "):
            schedule(cmd[4:])
        elif cmd == "list":
            list_containers()
        else:
            print("Commands: run <command>, list, exit")
