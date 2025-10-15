# import os

# def create_volume(container_id):
#     host_path = f"/home/user/EduDistOS/volumes/{container_id}"
#     os.makedirs(host_path, exist_ok=True)
#     os.system(f"mount --bind {host_path} /containers/{container_id}/data")



# storage_manager.py
import os, shutil

def bind_mount(source, destination):
    if not os.path.exists(destination):
        os.makedirs(destination)
    for file in os.listdir(source):
        src = os.path.join(source, file)
        dst = os.path.join(destination, file)
        if os.path.isfile(src):
            shutil.copy(src, dst)
    print(f"[Storage] Mounted {source} -> {destination}")

if __name__ == "__main__":
    bind_mount("./host_data", "./container_data")
