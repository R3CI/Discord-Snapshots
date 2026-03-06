# REQUIRMENTS

# Node JS
# npm install -g @electron/asar
# npm install -g js-beautify

# Python
# pip install curl_cffi
# pip install tqdm
# pip install dataclasses
# pip install pathlib
# pip install zipfile

# Other
# 7zip (IN PATH) 

# r3ci is finally gonna respect the pep rules ???!?!?!?
import curl_cffi
from tqdm import tqdm
from dataclasses import dataclass
from pathlib import Path
import zipfile
import os
import uuid
import shutil
import subprocess
import threading
import time
import sys
import platform 
import datetime

@dataclass
class Folders:
    root: str = os.getcwd()
    temp: str = os.path.join(root, 'temp')

    installer: str = os.path.join(root, 'snapshots', 'installer')
    installer_raw: str = os.path.join(root, 'snapshots', 'installer', 'raw')
    installer_unpacked_layer1: str = os.path.join(root, 'snapshots', 'installer', 'unpacked_layer1')
    installer_unpacked_layer2: str = os.path.join(root, 'snapshots', 'installer', 'unpacked_layer2')

    app: str = os.path.join(root, 'snapshots', 'app')
    app_raw: str = os.path.join(root, 'snapshots', 'app', 'raw')
    app_unpacked: str = os.path.join(root, 'snapshots', 'app', 'unpacked')

    if platform.system() == "Windows":
        asar: str = str(Path.home() / "AppData" / "Roaming" / "npm" / "asar.cmd")
        jsbeautify: str = str(Path.home() / "AppData" / "Roaming" / "npm" / "js-beautify.cmd")
    else:
        asar: str = "asar"
        jsbeautify: str = "js-beautify"

for folder in [
    Folders.root,
    Folders.installer,
    Folders.installer_raw,
    Folders.installer_unpacked_layer1,
    Folders.installer_unpacked_layer2,
    Folders.app,
    Folders.app_raw,
    Folders.app_unpacked
]:
    os.makedirs(folder, exist_ok=True)

class Utils:
    def uniexcract(i, o):
        os.makedirs(o, exist_ok=True)
        try:
            subprocess.run(['7z', 'x', i, f'-o{o}', '-y'], check=True)
            print(f'Extracted {i} to {o}')
        except subprocess.CalledProcessError as e:
            print(f'7-Zip extraction failed: {e}')

    def extract_version(file:str):
        version = file.replace('Discord-', '').replace('-full.nupkg', '')
        return version
    
    def extract_asar(i, o):
        subprocess.run([Folders.asar, "extract", i, o], check=True)

    def beautify_tree(directory):
        extensions = (".js", ".html", ".css", ".json", ".jsx", ".ts", ".tsx")

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(extensions):
                    full = os.path.join(root, file)

                    try:
                        subprocess.run(
                            [Folders.jsbeautify, "-r", "-f", full],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=True
                        )
                    except subprocess.CalledProcessError:
                        pass

class DiscordTrolly:
    def __init__(self):
        self.sess = curl_cffi.requests.session.Session(impersonate='chrome142')
        self.sess.headers.update({
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://www.google.com/',
            'sec-ch-ua': '"Chromium";v="142", "Not-A.Brand";v="24", "Google Chrome";v="142"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        })
    
    def get_latest_installer(self, save_dir):
        try:
            url = 'https://discord.com/api/downloads/distributions/app/installers/latest'
            params = {
                'channel': 'stable',
                'platform': 'win',
                'arch': 'x64'
            }

            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, 'DiscordSetup.exe')

            r = self.sess.get(url, params=params, stream=True, timeout=120)
            r.raise_for_status()

            total_size = int(r.headers.get('Content-Length', 0))
            chunk_size = 1024 * 1024

            with open(filepath, 'wb') as f, tqdm(
                total=total_size, unit='B', unit_scale=True, desc='Downloading installer', miniters=1
            ) as progress:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))

            print(f'Download complete: {filepath}')
            return True
        
        except Exception as e:
            print(f'Error downloading installer: {e}')
            return False

trolly = DiscordTrolly()

def installer_loop():
    while True:
        datetime_rn = datetime.datetime.now().strftime('%Y-%m-%d')
        raw_save_dir = os.path.join(Folders.installer_raw, datetime_rn)
        succedded = trolly.get_latest_installer(raw_save_dir)
        if succedded:
            tempdir1 = os.path.join(Folders.temp, uuid.uuid4().hex)
            os.makedirs(tempdir1, exist_ok=True)
            Utils.uniexcract(os.path.join(raw_save_dir, 'DiscordSetup.exe'), tempdir1)
            version = None
            for file in os.listdir(tempdir1):
                if file.startswith('Discord-'):
                    version = Utils.extract_version(file)
                    break
            
            if not version:
                print('Failed to extract version')
                continue

            layer1_save_dir = os.path.join(Folders.installer_unpacked_layer1, version)
            if not os.path.exists(layer1_save_dir):
                os.makedirs(layer1_save_dir, exist_ok=True)

                for file_name in os.listdir(tempdir1):
                    src_path = os.path.join(tempdir1, file_name)
                    dst_path = os.path.join(layer1_save_dir, file_name)
                    
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dst_path)
                    elif os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

            shutil.rmtree(tempdir1, ignore_errors=True)

            tempdir2 = os.path.join(Folders.temp, uuid.uuid4().hex)
            layer2_save_dir = os.path.join(Folders.installer_unpacked_layer2, version)
            raw_app_save_dir = os.path.join(Folders.app_raw, version)
            unpacked_app_save_dir = os.path.join(Folders.app_unpacked, version)

            os.makedirs(tempdir2, exist_ok=True)
            os.makedirs(layer2_save_dir, exist_ok=True)
            os.makedirs(raw_app_save_dir, exist_ok=True)
            os.makedirs(unpacked_app_save_dir, exist_ok=True)

            for file_name in os.listdir(layer1_save_dir):
                if file_name.startswith('Discord-'):
                    with zipfile.ZipFile(os.path.join(layer1_save_dir, file_name), 'r') as zip_ref:
                        zip_ref.extractall(layer2_save_dir)

                    for root, dirs, files in os.walk(layer2_save_dir):
                        for file in files:
                            if file.lower().endswith('.asar'):
                                full_path = os.path.join(root, file)
                                asar_unpack_dir = os.path.join(unpacked_app_save_dir, os.path.splitext(file)[0])
                                os.makedirs(asar_unpack_dir, exist_ok=True)
                                Utils.extract_asar(full_path, asar_unpack_dir)
                                Utils.beautify_tree(unpacked_app_save_dir)
                                shutil.copy2(full_path, raw_app_save_dir)
                                shutil.rmtree(tempdir2, ignore_errors=True)


        #time.sleep(600)
        break

#threading.Thread(target=installer_loop, daemon=True).start()

#while True:
#    time.sleep(1)

installer_loop()