import yaml
from tavily import TavilyClient
def get_config():
    with open("D:/config.yaml","r") as file:
        config = yaml.safe_load(file)
    return config


TAVILY_API_KEY = get_config()['TAVILY_API_KEY']
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def search(query:str):
    response = tavily_client.search(query)