import pytest
import json
from log_server import app, create_connection
from unittest import mock

@pytest.fixture
def client():
    app.testing = True
    client = app.test_client()

    # 設定測試資料庫連線
    db_connection = create_connection()
    if db_connection is None:
        pytest.fail("資料庫連線失敗，無法進行測試")  # 若連線失敗則停止測試

    cursor = db_connection.cursor()

    # 清空並建立測試資料表
    cursor.execute("DROP TABLE IF EXISTS log_data;")
    cursor.execute("""
        CREATE TABLE log_data (
            ID INT PRIMARY KEY AUTO_INCREMENT,
            HOST_NAME VARCHAR(32),
            HOST_IP VARCHAR(15),
            SYSTEM_TYPE VARCHAR(20),
            LEVEL VARCHAR(6),
            PROCESS_NAME VARCHAR(64),
            CONTENT VARCHAR(512),
            LOG_TIME DATETIME,
            TIMESTAMP TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db_connection.commit()

    yield client

    # 測試完後關閉資料庫連線
    db_connection.close()

def test_index(client):
    """測試根路徑是否正確提供 index.html"""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'<!DOCTYPE html>' in rv.data  # 確認回應是否包含 HTML

def test_search_logs_no_params(client):
    # 測試在沒有參數的情況下，/search 返回所有日誌
    response = client.get('/search')
    data = json.loads(response.data)

    print("Response status code:", response.status_code)
    print("Response data:", data)

    assert response.status_code == 200  # 確認狀態碼是200
    # assert len(data) > 0  # Confirm that the returned logs are not empty

def test_search_logs_with_params(client):
    # 測試在帶有參數的情況下，/search 返回符合條件的日誌
    response = client.get('/search', query_string={'host_name': 'example'})
    data = json.loads(response.data)

    print("Response status code:", response.status_code)
    print("Response data:", data)

    assert response.status_code == 200  # 確認狀態碼是200
    # assert len(data) > 0  # Confirm that the returned logs match the conditions

def test_save_log_success(client):
    # 測試成功保存日誌
    log_data = {
        'HOST_NAME': 'example_host',
        'HOST_IP': '192.168.0.1',
        'SYSTEM_TYPE': 'example_system',
        'LEVEL': 'INFO',
        'PROCESS_NAME': 'example_process',
        'CONTENT': 'This is a log message',
        'LOG_TIME': '2024-08-30 12:00:00'
    }
    response = client.post('/save-log', json=log_data)

    print("Response status code:", response.status_code)
    print("Response data:", response.data.decode('utf-8'))

    assert response.status_code == 201  # 確認狀態碼是201，表示創建成功
    assert 'success' in response.data.decode('utf-8')  # 確認返回訊息中包含'success'


def test_save_log_missing_field(client):
    """測試保存日誌時缺少必要字段"""
    data = {
        'HOST_NAME': 'localhost',
        'HOST_IP': '127.0.0.1',
        'SYSTEM_TYPE': 'Linux',
        'LEVEL': 'INFO',
        'PROCESS_NAME': 'test_process',
        'CONTENT': 'This is a test log entry'
        # Missing LOG_TIME
    }
    rv = client.post('/save-log', json=data)
    assert rv.status_code == 400
    assert b'error' in rv.data

def test_save_log_invalid_data(client):
    """測試保存日誌時的無效數據"""
    data = {
        'HOST_NAME': 'localhost',
        'HOST_IP': '127.0.0.1',
        'SYSTEM_TYPE': 'Linux',
        'LEVEL': 'INVALID',  # Invalid log level
        'PROCESS_NAME': 'test_process',
        'CONTENT': 'This is a test log entry',
        'LOG_TIME': '2024-08-30 12:00:00'
    }
    rv = client.post('/save-log', json=data)
    assert rv.status_code == 402
    assert b'error' in rv.data

def test_save_log_invalid_time_format(client):
    """測試保存日誌時的長度錯誤"""
    data = {
        'HOST_NAME': 'localhost' * 10,
        'HOST_IP': '127.0.0.1',
        'SYSTEM_TYPE': 'Linux',
        'LEVEL': 'INFO',
        'PROCESS_NAME': 'test_process',
        'CONTENT': 'This is a test log entry',
        'LOG_TIME': '2024-08-30 12:00:00'
    }
    rv = client.post('/save-log', json=data)
    assert rv.status_code == 402
    assert b'error' in rv.data
def test_database_connection_failure(client):
    """模擬資料庫連線失敗的情況"""
    with mock.patch('log_server.create_connection', return_value=None):
        data = {
            'HOST_NAME': 'localhost',
            'HOST_IP': '127.0.0.1',
            'SYSTEM_TYPE': 'Linux',
            'LEVEL': 'INFO',
            'PROCESS_NAME': 'test_process',
            'CONTENT': 'This is a test log entry',
            'LOG_TIME': '2024-08-30 12:00:00'
        }
        rv = client.post('/save-log', json=data)
        assert rv.status_code == 502
        assert b'Database connection failed' in rv.data


