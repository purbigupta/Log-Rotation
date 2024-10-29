#!/usr/bin/env python3.12

import os
import pwd
import zipfile
import shutil
import gzip
import logging
import time
from datetime import datetime, timedelta
import configparser
import getpass
import argparse

log_folder = os.path.join(os.path.expanduser('~'), 'Log-Rotation/course_project/log')
archive_folder = os.path.join(os.path.expanduser('~'), 'Log-Rotation/course_project/archived_logs')
status_log = os.path.join(os.path.expanduser('~'), 'Log-Rotation/rotation_status.log')
os.makedirs(archive_folder, exist_ok=True)

# Load configurations from log.cfg
config = configparser.ConfigParser()
config.read(os.path.join(os.path.expanduser('~'), 'Log-Rotation/log.cfg'))

# Argument Parsing
parser = argparse.ArgumentParser(description='Log rotation script')
parser.add_argument('--max_size_mb', type=int, help='Maximum log folder size in MB')
parser.add_argument('--retention_days', type=int, help="Days to retain archived logs")
parser.add_argument('--delegate', type=str, help="Delegate ownership of logs to another user")  

args = parser.parse_args()

# Prioritize args over config file
MAX_SIZE_MB = args.max_size_mb if args.max_size_mb else config.getint('Settings', 'MAX_SIZE_MB', fallback=100)
RETENTION_DAYS = args.retention_days if args.retention_days else config.getint('Settings', 'RETENTION_DAYS', fallback=7)

# Configure logging
logging.basicConfig(filename=status_log, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def delegate_ownership(new_owner):
    try:
        # Check if the new owner exists
        user_info = pwd.getpwnam(new_owner)
        user_id = user_info.pw_uid
        group_id = user_info.pw_gid
        
        # Change ownership of log files and archive files to new owner
        for folder in [log_folder, archive_folder]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                os.chown(file_path, user_id, group_id)
        
        logging.info(f"Ownership delegated to user: {new_owner}")
    except KeyError:
        logging.error(f"User {new_owner} does not exist.")
        exit(5)
    except Exception as e:
        logging.error(f"Error delegating ownership: {e}")
        exit(6)

def zip_and_delete_logs():
    try:
        logging.info("Zipping logs...")
        logging.info(f"Log folder path: {log_folder}")  # Add this line
        today = datetime.now().strftime('%Y-%m-%d')
        zip_filename = os.path.join(archive_folder, f'{today}_logs.zip')
        total_files = 0
        largest_file = None
        largest_size = 0

        with zipfile.ZipFile(zip_filename, 'w') as log_zip:
            for filename in os.listdir(log_folder):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_folder, filename)
                    file_size = os.path.getsize(file_path)
                    log_zip.write(file_path, arcname=filename)
                    os.remove(file_path)
                    total_files += 1
                    if file_size > largest_size:
                        largest_file = filename
                        largest_size = file_size

        if total_files > 0:
            logging.info(f"Total number of zipped files: {total_files}")
            logging.info(f"Largest zipped file: {largest_file} with size {largest_size} bytes, created on {today}.")
        else:
            logging.info("No files were zipped.")
    except Exception as e:
        logging.error(f"Error during zipping logs: {e}")
        exit(1)

    
def delete_old_archives():
    try:    
        retention_period = datetime.now() - timedelta(days=RETENTION_DAYS)
        for filename in os.listdir(archive_folder):
         file_path = os.path.join(archive_folder, filename)
        if filename.endswith('.zip'):
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_creation_time < retention_period:
                os.remove(file_path)
                print(f"Deleted old archive: {filename}")
    except Exception as e:
        logging.error(f"Error deleting old archives: {e}")
    exit(2)


def check_folder_size():
    try:
        total_size = sum(os.path.getsize(os.path.join(log_folder, f)) for f in os.listdir(log_folder))
        max_size_bytes = MAX_SIZE_MB * 1024 * 1024
        if total_size > max_size_bytes:
            logging.warning(f"Log folder size ({total_size} bytes) exceeds {MAX_SIZE_MB} MB.")
    except Exception as e:
        logging.error(f"Error checking folder size: {e}")
    exit(3)


if getpass.getuser() != 'logmanager':
    logging.error(f"Access Denied: Only user named 'logmanager' is allowed to run script.")
    exit(4)
try:
    zip_and_delete_logs()
    delete_old_archives()
    check_folder_size()
except Exception as e:
    logging.error(f"Unexpected error in main: {e}")
    exit(99)

if __name__ == '__main__':
    # TODO: add other parts here like getuser function 

    # Parse delegate argument
    args = parser.parse_args()
    if args.delegate:
        delegate_ownership(args.delegate)
    else:
        try:
            zip_and_delete_logs()
            delete_old_archives()
            check_folder_size()
        except Exception as e:
            logging.error(f"Unexpected error in main: {e}")
            exit(99)