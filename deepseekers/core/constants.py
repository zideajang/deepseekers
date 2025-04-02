import yaml
__CTX_VARS_NAME__ = "context"

# 获取 deepseek API
def get_config():
    with open("D:/config.yaml","r") as file:
        config = yaml.safe_load(file)
    return config

DEEPSEEK_API_KEY = get_config()['DEEPSEEK_API_KEY']
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'