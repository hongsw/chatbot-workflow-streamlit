#!/bin/bash

exec > >(tee /var/log/user-data.log | logger -t user-data) 2>&1

APP_DIR="/home/ubuntu/streamlit-app"
REPO="https://github.com/hongsw/chatbot-workflow-streamlit.git"

echo "===== Update ====="
apt-get update -y
apt-get install -y python3-pip python3-venv git

echo "===== Clone app ====="
mkdir -p $APP_DIR
git clone $REPO $APP_DIR
chown -R ubuntu:ubuntu $APP_DIR

echo "===== Create venv ====="
sudo -u ubuntu python3 -m venv $APP_DIR/venv
sudo -u ubuntu $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u ubuntu $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

echo "===== Create systemd service ====="
cat > /etc/systemd/system/streamlit.service <<EOF
[Unit]
Description=Streamlit App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "===== Enable & Start service ====="
systemctl daemon-reload
systemctl enable streamlit.service
systemctl start streamlit.service

echo "===== DONE ====="
