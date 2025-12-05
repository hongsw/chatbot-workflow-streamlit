#!/bin/bash

# 로그 파일 설정
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "========== Streamlit App 자동 설치 시작 =========="
date

# Step 1: 시스템 업데이트
echo "Step 1: 시스템 업데이트..."
apt-get update -y
apt-get upgrade -y

# Step 2: 필수 패키지 설치
echo "Step 2: 필수 패키지 설치..."
apt-get install -y python3-pip python3-venv git

# Step 3: 앱 디렉토리 생성
echo "Step 3: 앱 디렉토리 생성..."
APP_DIR="/home/ubuntu/streamlit-app"
mkdir -p $APP_DIR
cd $APP_DIR

# Step 4: Git 저장소 클론
echo "Step 4: Git 저장소 클론..."
# ⚠️ 본인의 GitHub 저장소 URL로 변경하세요
GIT_REPO="https://github.com/hongsw/chatbot-workflow-streamlit.git"
git clone $GIT_REPO .

# 소유권 변경
chown -R ubuntu:ubuntu $APP_DIR

# Step 5: Python 가상환경 생성
echo "Step 5: Python 가상환경 생성..."
sudo -u ubuntu python3 -m venv $APP_DIR/venv

# Step 6: Python 패키지 설치
echo "Step 6: Python 패키지 설치..."
sudo -u ubuntu $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u ubuntu $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
# Step 7: Streamlit 백그라운드 실행
echo "Step 7: Streamlit 앱 시작..."
cd $APP_DIR
nohup sudo -u ubuntu $APP_DIR/venv/bin/streamlit run $APP_DIR/app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  > /home/ubuntu/streamlit.log 2>&1 &

echo "========== 설치 완료 =========="
echo "Streamlit 앱이 백그라운드에서 실행 중입니다"
date