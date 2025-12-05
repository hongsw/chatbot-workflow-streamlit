#!/bin/bash

exec > >(tee /var/log/user-data.log) 2>&1

APP_DIR="/home/ubuntu/streamlit-app"
GIT_REPO="https://github.com/hongsw/chatbot-workflow-streamlit.git"

echo "[1] Updating system..."
apt-get update -y
apt-get install -y python3-pip python3-venv git

echo "[2] Preparing app directory..."
mkdir -p $APP_DIR
cd $APP_DIR
git clone $GIT_REPO .

chown -R ubuntu:ubuntu $APP_DIR

echo "[3] Creating virtual env..."
sudo -u ubuntu python3 -m venv $APP_DIR/venv
sudo -u ubuntu $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u ubuntu $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

echo "[4] Creating systemd service..."
cat <<EOF >/etc/systemd/system/streamlit.service
[Unit]
Description=Streamlit App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/streamlit run $APP_DIR/app.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "[5] Reloading systemd..."
systemctl daemon-reload

echo "[6] Starting Streamlit service (1회 실행)"
systemctl start streamlit.service

echo "========== DONE =========="
date
