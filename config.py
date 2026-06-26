import os
import configparser

CONFIG_FILE = "config.ini"

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config["database"] = {
            "host": "localhost",
            "port": "5432",
            "user": "postgres",
            "password": "MegaFon",
            "dbname": "gate_calculator"
        }
        with open(CONFIG_FILE, "w") as f:
            config.write(f)
    else:
        config.read(CONFIG_FILE)
    return config

def get_db_config():
    config = load_config()
    return dict(config["database"])