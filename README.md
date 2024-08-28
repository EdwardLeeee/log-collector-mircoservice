## log 收容微服務 （log collector microservice）
1. 提供能收容現行各系統 log 的統一框架。
2. 提供查詢各系統 log 的功能。
3. 以微服務形式提升可維護性與擴充性。

### 整體架構圖 (Overall Architecture Diagram)
![image](https://github.com/user-attachments/assets/37b8870d-2032-4425-b081-73c35eaa1a93)

#### processor
![image](https://github.com/user-attachments/assets/2a5d9c5f-82c7-4cc6-bb52-48ece1afffa3)

#### collector
![image](https://github.com/user-attachments/assets/dd7a83a9-f320-4979-822a-6f0f77673eac)

#### logger
![image](https://github.com/user-attachments/assets/1de54ecd-f563-4e5c-9313-bf2703a09637)

### 使用說明

請使用以下指令建立與運行container

#### 建立image
請在`/container/logger`下執行
`podman build -t logger .`

請在`/container/container`下執行
`podman build -t container .`

`podman pull mysql8.0`

#### 建立container
```
podman pod create log-collector-microservice -p 5050:5050 -p 5000:5000
podman run -d --pod log-collector-service --name collector collector:latest
podman run -d --pod log-collector-service --name logger logger:latest
podman run -d --pod log-collector-service --name mysql-db -e MYSQL_ROOT_PASSWORD=your-password -v /absolute-path-to-data/:/var/lib/mysql mysql:8.0
```

#### API 說明文件 UI
`podman run -d --name collector_swagger -p 8080:8080 -e SWAGGER_JSON=/foo/openapi.yaml -v /absolute-path-to/log-collector-microservice/container/collector/collector_openapi.yaml:/foo/openapi.yaml swaggerapi/swagger-ui`
`podman run -d --name logger_swagger -p 8081:8080 -e SWAGGER_JSON=/foo/openapi.yaml -v /absolute-path-to/log-collector-microservice/container/logger/logger_openapi.yaml:/foo/openapi.yaml swaggerapi/swagger-ui`

#### 查閱 Web UI
- log searching  請在瀏覽器輸入
`http://localhost:5000`
- collector API 說明
`http://loclahost:8080`
-logger API 說明
`http://localhost:8081`
