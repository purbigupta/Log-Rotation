#!/usr/bin/env python3.12

import os
import pwd
import zipfile
import logging
import time
from datetime import datetime, timedelta
import configparser
import getpass
import argparse

# Set base directory to the current working directory
base_folder = os.getcwd()
log_folder = os.path.join(base_folder, 'log')
archive_folder = os.path.join(base_folder, 'archived_logs')
status_log = os.path.join(base_folder, 'rotation_status.log')

# Ensure directories exist
os.makedirs(log_folder, exist_ok=True)
os.makedirs(archive_folder, exist_ok=True)

# Load configurations from log.cfg
config = configparser.ConfigParser()
config_file_path = os.path.join(base_folder, 'log.cfg')
config.read(config_file_path)

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
logging.basicConfig(filename=status_log, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Delegate ownership function
def delegate_ownership(new_owner):
    try:
        user_info = pwd.getpwnam(new_owner)
        user_id = user_info.pw_uid
        group_id = user_info.pw_gid

        for folder in [log_folder, archive_folder]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    os.chown(file_path, user_id, group_id)
                except PermissionError:
                    logging.error(f"Permission denied: Cannot change ownership of {file_path}.")
                except FileNotFoundError:
                    logging.error(f"File not found: {file_path}.")
        
        logging.info(f"Ownership delegated to user: {new_owner}")
    except KeyError:
        logging.error(f"User {new_owner} does not exist.")
        exit(5)
    except Exception as e:
        logging.error(f"Error delegating ownership: {e}")
        exit(6)

# Zip and delete logs function
def zip_and_delete_logs():
    try:
        logging.info("Zipping logs...")
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
            logging.info(f"Largest zipped file: {largest_file} with size {largest_size} bytes.")
        else:
            logging.info("No files were zipped.")
    except Exception as e:
        logging.error(f"Error during zipping logs: {e}")
        exit(1)

# Delete old archives function
def delete_old_archives():
    try:
        retention_period = datetime.now() - timedelta(days=RETENTION_DAYS)
        for filename in os.listdir(archive_folder):
            file_path = os.path.join(archive_folder, filename)
            if filename.endswith('.zip'):
                file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_creation_time < retention_period:
                    os.remove(file_path)
                    logging.info(f"Deleted old archive: {filename}")
    except Exception as e:
        logging.error(f"Error deleting old archives: {e}")
        exit(2)

# Check folder size function
def check_folder_size():
    try:
        total_size = sum(os.path.getsize(os.path.join(log_folder, f)) for f in os.listdir(log_folder))
        max_size_bytes = MAX_SIZE_MB * 1024 * 1024
        if total_size > max_size_bytes:
            logging.warning(f"Log folder size ({total_size} bytes) exceeds {MAX_SIZE_MB} MB.")
    except Exception as e:
        logging.error(f"Error checking folder size: {e}")
        exit(3)

# Main execution block
if __name__ == "__main__":
    if args.delegate:
        delegate_ownership(args.delegate)
    else:
        try:
            zip_and_delete_logs()
            delete_old_archives()
            check_folder_size()
            logging.info("Tasks completed successfully.")
        except Exception as e:
            logging.error(f"Unexpected error in main: {e}")
            exit(99)
