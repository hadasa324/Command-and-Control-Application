import os


class BaseConfig:
    SERVER_IP = '127.0.0.1'
    SERVER_PORT = 44444
    KEEP_ALIVE_INTERVAL = 20
    PAYLOAD_DIR = os.getcwd()
    CONFIG_PATH = os.path.abspath('config_client_file.py')
