import os

def create_volume(container_id):
    host_path = f"/home/user/EduDistOS/volumes/{container_id}"
    os.makedirs(host_path, exist_ok=True)
    os.system(f"mount --bind {host_path} /containers/{container_id}/data")
