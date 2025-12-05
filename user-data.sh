#!/bin/bash

exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "=== Streamlit auto setup ==="
date

apt-get update -y
apt-get install -y python3-pip python3-venv git

APP_DIR="/home/ubuntu/streamlit-app"
GIT_REPO="https://github.com/hongsw/chatbot-workflow-streamlit.git"

mkdir -p $APP_DIR
cd $APP_DIR
git clone $GIT_REPO .

chown -R ubuntu:ubuntu $APP_DIR

# venv
python3 -m venv $APP_DIR/venv
$APP_DIR/venv/bin/pip install --upgrade pip
$APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Run Streamlit (root로 실행)
nohup $APP_DIR/venv/bin/streamlit run $APP_DIR/app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  > /var/log/streamlit.log 2>&1 &

echo "=== DONE ==="
date
