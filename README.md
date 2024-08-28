## 整體架構圖 (Overall Architecture Diagram)
![image](https://github.com/user-attachments/assets/37b8870d-2032-4425-b081-73c35eaa1a93)

## log 收容微服務 （log collector microservice）
1. 提供能收容現行各系統 log 的統一框架。
2. 提供查詢各系統 log 的功能。
3. 以微服務形式提升可維護性與擴充性。

### 使用說明

請使用以下指令建立與運行container

#### 建立image
- 請在 `/container/logger` 下執行 `podman build -t logger .`

- 請在 `/container/container` 下執行 `podman build -t container .`

- `podman pull mysql8.0`

#### 建立container
請注意，我們建議您建立一資料夾用來存放 mysql-db 的資料，此資料夾絕對路徑即為下文中的 `<absolute path to data>`
```
podman pod create --name log-collector-microservice -p 5050:5050 -p 5000:5000
podman run -d --pod log-collector-service --name collector collector:latest
podman run -d --pod log-collector-service --name logger logger:latest
podman run -d --pod log-collector-service --name mysql-db 
              -e MYSQL_ROOT_PASSWORD=<your-password> 
              -v <absolute path to data>:/var/lib/mysql 
              mysql:8.0
```

#### 建立 database
1. `podman exec -it mysql-db bash`
2. `mysql -h 127.0.0.1 -u root -p`
3. 輸入建立 container 時設定之 `MYSQL_ROOT_PASSWORD`
4. 輸入以下命令建立 logger 連接之帳號
（請注意，此處之帳號密碼需與資料夾 `logger` 中的 `Dockerfile` 所帶入的環境變數一致，以下為預設之帳密）
  ```
  CREATE USER 'oraclelee'@'%' IDENTIFIED BY '0000';
  GRANT ALL PRIVILEGES ON logger.* TO 'oraclelee'@'%';
  ```
5. 輸入以下命令創建 database 與 table
   （請注意，此處之 database 與 table 名稱需與資料夾 `logger` 中的 `Dockerfile` 所帶入的環境變數一致，以下為預設之名稱）
  ```
  CREATE DATABASE IF NOT EXISTS logger;
  USE logger;
  CREATE TABLE IF NOT EXISTS log_data (
      ID INT AUTO_INCREMENT PRIMARY KEY,
      HOST_NAME VARCHAR(32),
      HOST_IP VARCHAR(15),
      SYSTEM_TYPE VARCHAR(20),
      LEVEL VARCHAR(6),
      PROCESS_NAME VARCHAR(64),
      CONTENT VARCHAR(512),
      LOG_TIME DATETIME,
      TIMESTAMP TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
  );
  ```

## processor

`proccessor.py` 是一個負責傳送客戶端各種 process 所產生的不同格式之 log 給資料庫的程式。
它會去讀資料夾 `config` 中的設定檔， 並依照給定設定傳送 JSON 格式資料給負責切割 Raw Data 的 microservice (collector).

### 使用說明

#### 安裝必要套件
```
sudo apt update
sudo apt install pip
pip install requests
pip install watchdog
pip install pyyaml
```
#### 執行程式

在執行程式前需自行至程式 main function 中，修改 config.cfg 及 offest.json 之位置，以及 collector 的 URL。
```python3
def main():
    config_file = '<path to config.cfg>'
    offsets_file ='<path to offset.json>'
    # ex. offsets_file =f'/home/oraclelee/Desktop/log-collector-microservice/config/offsets{date.today()}.json'
    collector_url = '<collector URL>'  # 將URL變成參數
```

修改後在執行以下指令：

`python3 processor.py`


## API 說明文件 UI
collector swagger
```
podman run -d --name collector_swagger -p 8080:8080 
                -e SWAGGER_JSON=/foo/openapi.yaml 
                -v <absolute path to collector_openapi.yaml>:/foo/openapi.yaml 
                swaggerapi/swagger-ui
```
logger swagger 
```
podman run -d --name logger_swagger -p 8081:8080 
                -e SWAGGER_JSON=/foo/openapi.yaml 
                -v <absolute path to logger_openapi.yaml>:/foo/openapi.yaml 
                swaggerapi/swagger-ui
```
#### 查閱 Web UI
- log searching  請在瀏覽器輸入
`http://localhost:5000`
- collector API 說明
`http://loclahost:8080`
- logger API 說明
`http://localhost:8081`
