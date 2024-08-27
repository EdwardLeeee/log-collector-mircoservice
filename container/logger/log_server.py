from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
import configparser
from mysql.connector import Error
from flask_cors import CORS
import os
# 前端 GET
app = Flask(__name__, static_folder='public', template_folder='templates')
CORS(app)

@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/search', methods=['GET'])
def search_logs():
    host_name = request.args.get('host_name')
    host_ip = request.args.get('host_ip')
    system_type = request.args.get('system_type')
    level = request.args.getlist('level')  # 使用 getlist 取得多個值
    log_time_start = request.args.get('log_time_start')
    log_time_end = request.args.get('log_time_end')

    query = 'SELECT * FROM log_data WHERE 1=1'
    params = []

    if host_name:
        query += " AND HOST_NAME LIKE %s"
        params.append(f"%{host_name}%")
    if host_ip:
        query += " AND HOST_IP LIKE %s"
        params.append(f"%{host_ip}%")
    if system_type:
        query += " AND SYSTEM_TYPE LIKE %s"
        params.append(f"%{system_type}%")
    if level:
        levels_placeholder = ', '.join(['%s'] * len(level))
        query += f" AND LEVEL IN ({levels_placeholder})"
        params.extend(level)
    if log_time_start and log_time_end:
        query += " AND LOG_TIME BETWEEN %s AND %s"
        params.append(log_time_start)
        params.append(log_time_end)
    elif log_time_start:
        query += " AND LOG_TIME >= %s"
        params.append(log_time_start)
    elif log_time_end:
        query += " AND LOG_TIME <= %s"
        params.append(log_time_end)

    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            connection.close()
            return jsonify(results), 200
        else:
            return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 接收collector post

# 從設定檔讀取配置文件
config = configparser.ConfigParser()
config.read('db_config.txt')

db_config = {
    'user': config.get('DEFAULT', 'user'),
    'password': config.get('DEFAULT', 'password'),
    'host': config.get('DEFAULT', 'host'),
    'database': config.get('DEFAULT', 'database'),
}
'''
#  從環境變數讀取配置文件
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}
'''
def check_legal_data(data):
    errors = []
    validations = { # db format 參數
        'HOST_NAME': 32,
        'HOST_IP': 15,
        'LEVEL': 5,
        'SYSTEM_TYPE': 20,
        'PROCESS_NAME': 64,
        'CONTENT': 512,
        'LOG_TIME': 19
    }

    for field, max_len in validations.items():
        if len(data.get(field, '')) > max_len:
            errors.append(f'{field} 超過 {max_len} 個字符')

    if errors:
        print('Wrong data format')

    return errors


#創立會回傳連接而且會在server打印訊息
def create_connection():
    try:
        # mysql.connector.connect()是建立連接，裡面是連接的相關資訊
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    # try 失敗之後 印出錯誤訊息
    except Error as e:#Error 是錯誤的類別
        print("Error while connecting to MySQL", e)
        return None

def check_miss(data):
    # 檢查資料是否殘缺
    required_fields = ['HOST_NAME', 'HOST_IP', 'SYSTEM_TYPE', 'LEVEL', 'PROCESS_NAME', 'CONTENT', 'LOG_TIME']
    miss_field = []
    for field in required_fields:
        if field not in data:
            miss_field.append(field)
    if miss_field :
        print(f'Missing field: {miss_field}')

    return miss_field

# routing路徑為/log 用HTTP的post
@app.route('/save-log', methods=['POST'])
def log():
    # data為client打來的JSON格式資料
    # {"HOST_NAME":"XXXX" , "HOST_IP":"XXXX",.....}
    data = request.get_json()
    #檢查是否資料缺失
    missing_field = check_miss(data)
    if missing_field:
        return jsonify({'status': 'error', 'message': f'collector missing field {missing_field}'}), 400
    
    #檢查數據是否合法
    data_illegal = check_legal_data(data)
    if data_illegal:
        return jsonify({'status': 'error', 'message': f'illegal data  {data_illegal}'}), 402
    
    #無資料殘缺
    try:
        connection = create_connection()
        if connection:
            #創一個游標，用來輸入sql指令
            cursor = connection.cursor()

            #%s是實際要插入的值,參數化input
            input_order = """
            INSERT INTO log_data (HOST_NAME, HOST_IP, SYSTEM_TYPE, LEVEL, PROCESS_NAME, CONTENT, LOG_TIME)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            #執行
            #data是request進來的JSON，{"HOST_NAME":"XX","HOST_IP":"XX"}
            cursor.execute(input_order, (
                data['HOST_NAME'], data['HOST_IP'], data['SYSTEM_TYPE'], data['LEVEL'],
                data['PROCESS_NAME'], data['CONTENT'], data['LOG_TIME']
            ))

            #把cursor做的事提交
            #在執行 INSERT、UPDATE 或 DELETE 操作後，需要調用 commit() 方法來提交這些變更。
            #如果不調用 commit()，這些變更將不會被保存到資料庫中，並且在連接關閉時將被回滾。
            connection.commit()
            cursor.close()
            connection.close()
            return jsonify({'status': 'success', 'message': 'Log entry added successfully'}), 201

        #連接失敗，告訴client
        #原因: (1)sql 帳號密碼錯誤 (2)sql service 沒開
        else:
            return jsonify({'status': 'error', 'message': 'Database connection failed'}), 502
   #非資料庫連接錯誤:logger 的 (1) sql 指令錯誤 (2) python code 寫錯了
    except Error as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    #生產環境要把debug拿掉，host 0000表示接受所有的ip
    #thread表示多線程
    app.run(host='0.0.0.0', port=5000,threaded=True)
    ##GET成功200
    ##POST成功201
    ##data格式缺失 400
    ##data格式錯誤 402
    ##連接失敗500
    ##非連接問題失敗(sql or python 寫錯了)500
