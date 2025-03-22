import os
import pickle
from abc import ABC,abstractmethod
from pathlib import Path
from typing import Dict,Any,Union,List,Callable,Optional
from contextlib import contextmanager
from functools import wraps

from deepseekers.core import Agent
from deepseekers.core.utils import is_snake_case
from pydantic import BaseModel,Field

# TODO Tool
@contextmanager
def get_project(proj:"Project"):
    try:
        proj.setup()
        yield proj
    finally:
        if proj:
            proj.clean()

class Project(ABC):
    def __init__(self,
                 name:str,
                 description:Union[str,Callable[...,str]],
                 workspace_dir:str|Path,
                 pm:Agent|None = None,
                 temp_dir:str|Path|None = None,
                 is_cache:bool = False,
                 tools: Union[List[Union[str,Callable]]|None]=None):
        
        self.name = name
        self.description = description
        self.pm = pm
        self.is_cache = is_cache
        self.workspace_dir = workspace_dir
        self.temp_dir = temp_dir or f"{workspace_dir}/temp"

        self._context = {
            'name':name,
            'description':description,
            'pm':pm
        }

        if self.is_cache:
            if self.workspace_dir:
                cache_folder_path = os.path.join(self.workspace_dir, "cache")
                if not os.path.exists(cache_folder_path):
                    os.makedirs(cache_folder_path)
                
                self.cache_file_path = os.path.join(cache_folder_path, f"{self.name}.pickle")
                self.load_project(self.cache_file_path)
            else:
                raise ValueError(f"请指定 workspace_dir")

        
        self.tools = tools or []

    @property
    def context(self):
        # TODO
        return self._context

    def load_project(self,file_path):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                self._context = pickle.load(file)
        else:
            with open(file_path, 'wb') as file:
                pickle.dump(self._context, file)

    @abstractmethod
    def setup(self):
        raise NotImplementedError()

    def step(self,**inject_kwargs):
        def decorator(func):
            @wraps(func)
            def wrapper(*args,**kwargs):
                all_kwargs = {**inject_kwargs, **kwargs}
                if self.is_cache and func.__name__ in self._context.keys() and self._context[func.__name__]:

                    return self._context[func.__name__]
                
                result = func(self,*args, **all_kwargs)
                self._context[func.__name__] = result
                if self.is_cache:
                    with open(self.cache_file_path, 'wb') as file:
                        pickle.dump(self._context, file)
                return result
            return wrapper
        return decorator

    @abstractmethod
    def clean(self):
        raise NotImplementedError()
    
