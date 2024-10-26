#!/usr/bin/env python3

import os
import zipfile
import shutil
import gzip
import logging
import time
from datetime import datetime, timedelta
import configparser

log_folder = os.path.join(os.path.expanduser('~'), 'Log-Rotation/course_project/log')
archive_folder = os.path.join(os.path.expanduser('~'), 'Log-Rotation/course_project/archived_logs')
os.makedirs(archive_folder, exist_ok=True)

def zip_and_delete_logs():
    print("Zipping logs...")
    print(f"Found files: {os.listdir(log_folder)}")
    today = datetime.now().strftime('%Y-%m-%d')
    zip_filename = os.path.join(archive_folder, f'{today}_logs.zip')
    with zipfile.ZipFile(zip_filename, 'w') as log_zip:
        for filename in os.listdir(log_folder):
            if filename.endswith('.log'):
                file_path = os.path.join(log_folder, filename)
                log_zip.write(file_path, arcname=filename)
                os.remove(file_path)

zip_and_delete_logs()