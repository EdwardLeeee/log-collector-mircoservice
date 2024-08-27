# 使用官方 Python 基礎映像
FROM python:3.10

# 設定工作目錄
WORKDIR /app

# 複製當前目錄的內容到工作目錄中
COPY . .

# 安裝所需的 Python 包
RUN pip install --no-cache-dir Flask==3.0.3 mysql-connector-python==9.0.0 flask-cors==4.0.1

# 設定環境變數
ENV DB_USER=oraclelee DB_PASSWORD=0000 DB_HOST=localhost DB_NAME=logger

# 暴露 Flask 預設的端口
EXPOSE 5000

# 啟動 Flask 應用程序
CMD python3 log_server.py
