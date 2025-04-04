import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys

def get_config():
    """
    从 YAML 格式的字符串中读取数据。

    Args:
        yaml_string (str): 包含 YAML 数据的字符串。

    Returns:
        dict 或 list 或 None: 如果成功解析，则返回解析后的 YAML 数据；
                             如果解析失败，则返回 None。
    """
    try:
        with open("./config.yaml", 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except yaml.YAMLError as e:
        print(f"错误：解析 YAML 字符串失败：{e}")
        return None
def setup_selenium_driver(headless: bool = False)-> webdriver.Chrome:
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless") 
    chromedriver = get_config()['CHROMEDRIVER']
    driver = webdriver.Chrome(service=Service(chromedriver))
    return driver


# driver.get("https://www.python.org")
# print(driver.title)