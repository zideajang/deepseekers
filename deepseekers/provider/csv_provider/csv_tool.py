import pandas as pd
from deepseekers.provider import BaseProviderContext
from deepseekers.provider.csv_provider import CSVProviderContext

def provide_context(context:BaseProviderContext,csv_path:str|pd.DataFrame):
    
    """读取 csv 文件获取数据
    """
    context = CSVProviderContext()
    if isinstance(csv_path,str):
        data = pd.read_csv(csv_path)
    elif isinstance(csv_path,pd.DataFrame):
        data = csv_path
    else:
        raise TypeError("csv_path 必须是字符串路径或 pandas DataFrame 对象")
    context = BaseProviderContext(data=data,)
    return [context]

def missing_value_analysis(context:BaseProviderContext,field_name:str):
    """识别列中缺失值的数量、比例和分布情况"""
    df = context.data
