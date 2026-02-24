# 1. 使用輕量版 Python 作為基底
FROM python:3.10-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
# 2. 設定容器內的工作目錄
WORKDIR /app

RUN pip install chat-downloader@git+https://github.com/Indigo128/chat-downloader
# 3. 複製套件清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# 4. 複製所有程式碼到容器內
COPY . .

# 5. 執行 Python 程式
CMD ["python", "server.py"]