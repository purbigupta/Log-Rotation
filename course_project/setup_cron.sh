#!/bin/bash

script_path="$(cd "$(dirname "$0")" && pwd)/log_rotation.py"

echo "Script path is: $script_path"

(crontab -l | grep -F "log_rotation.py") || {
  (crontab -l 2>/dev/null; echo "0 0 * * * python3 $script_path") | crontab -
  echo "Cron job added to run log_rotation.py daily at midnight."
}
