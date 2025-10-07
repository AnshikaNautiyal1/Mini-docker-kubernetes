import psutil, time

while True:
    print(f"CPU: {psutil.cpu_percent()}% | MEM: {psutil.virtual_memory().percent}%")
    time.sleep(2)
