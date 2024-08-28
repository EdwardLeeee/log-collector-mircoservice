## 整體架構圖 (Overall Architecture Diagram)
![image](https://github.com/user-attachments/assets/37b8870d-2032-4425-b081-73c35eaa1a93)

## log 收容微服務 （log collector microservice）
1. 提供能收容現行各系統 log 的統一框架。
2. 提供查詢各系統 log 的功能。
3. 以微服務形式提升可維護性與擴充性。

### 使用說明

請使用以下指令建立與運行container

#### 建立image
- 請在`/container/logger`下執行
`podman build -t logger .`

- 請在`/container/container`下執行
`podman build -t container .`

- `podman pull mysql8.0`

#### 建立container
```
podman pod create --name log-collector-microservice -p 5050:5050 -p 5000:5000
podman run -d --pod log-collector-service --name collector collector:latest
podman run -d --pod log-collector-service --name logger logger:latest
podman run -d --pod log-collector-service --name mysql-db 
              -e MYSQL_ROOT_PASSWORD=<your-password> 
              -v <absolute path to data>:/var/lib/mysql 
              mysql:8.0
```
## processor

proccessor.py是一個負責傳送客戶端各種 process 所產生的不同格式之 log 給資料庫的程式。
它會去讀資料夾 config 中的設定檔， 並依照給定設定傳送 JSON 格式資料給負責切割 Raw Data 的 microservice(collector).

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
![image](https://github.com/user-attachments/assets/5f060168-8012-41cc-8e8f-780064aa2231)

修改後在執行以下指令：

`python3 processor`


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
