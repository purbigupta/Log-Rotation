#!/bin/bash

script_path="$(cd "$(dirname "$0")" && pwd)/log_rotation.py"

echo "Script path is: $script_path"

(crontab -l | grep -F "log_rotation.py") || {
  (crontab -l 2>/dev/null; echo "0 0 * * * python3 $script_path") | crontab -
  echo "Cron job added to run log_rotation.py daily at midnight."
}

service_file="/etc/systemd/system/log_rotation.service"
echo "[Unit]
Description=Log Rotation Service

[Service]
ExecStart=$(which python3) $(pwd)/log_rotation.py

[Install]
WantedBy=multi-user.target" | sudo tee $service_file

sudo systemctl enable log_rotation.service
sudo systemctl start log_rotation.service