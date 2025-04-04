from time import sleep
import uuid

import atexit

import docker
import docker.errors
from docker.models.containers import Container
from docker.errors import ImageNotFound
from hashlib import md5

from pathlib import Path
from typing import Optional,Union,List,Self,Type
from types import TracebackType

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.columns import Columns

from azent.extension.coding.base import CodeExecutor,CodeExtractor
from azent.core.message import CodeMessage,BaseMessage
from azent.result.code_result import CodeResult
from azent.extension.coding.utils import _cmd,TIMEOUT_MSG

from loguru import logger

logger.add("docker.log",format="{time} {level} {message}")

# TODO
default_python_docker_image:str = "python:3-slim"
code_excute_time_out:int = 60
__all__ = ("DockerCodeExcutor")


console = Console()

def _wait_for_ready(container:Container,timeout:int=60,stop_time:int=0.1)->None:
    elapsed_time = 0
    while container.status != "running" and elapsed_time < timeout:
        sleep(stop_time)
        elapsed_time += stop_time
        container.reload()
        continue
    if container.status != "running":
        raise ValueError("容器启动没成功呀! 😢")


class DockerCodeExcutor(CodeExtractor):

    def __init__(self,
                 image:str = default_python_docker_image,
                 container_name:Optional[str] = None,
                 timeout:int = code_excute_time_out,
                 work_dir:Union[Path,str] = Path('.'),
                 auto_remove:bool = True,
                 stop_container:bool = True,
                 ):
        """A code executer
        
        Args:
            image(_type_): docker 的镜像，默认是 python:3-slim 也就是运行 python 的环境的镜像
            timeout,
            work_dir: 也就是运行 docker 的映射的工作目录，默认是当前目录
        """        

        if timeout < 1:
            raise ValueError("超时时间设置时间需要大于 1")

        if isinstance(work_dir,str):
            work_dir = Path(work_dir)

        if not work_dir.exists():
            raise ValueError(f"工作目录 {work_dir} 不存在")
        
        # 获取 docker 的客户端
        client = docker.from_env()

        # 检查 docker 镜像是否存在
        try:
            client.images.get(image)
        except ImageNotFound:
            logger.info(f"请加载 {image} 镜像...")
            console.print(f"请加载 {image} 💿 镜像...")
            client.images.pull(image)
        
        # 设置docker容器名字
        if container_name is None:
            container_name = f"deepseekers-code-exec-{uuid.uuid4()}"

        # 创建docker容器
        self._container = client.containers.create(
            image,
            name=container_name,
            entrypoint="/bin/sh",
            tty=True,
            auto_remove=auto_remove,
            volumes={str(work_dir.resolve()): {"bind":"/workspace","mode":"rw"}},
            working_dir="/workspace",
        )

        # 启动容器
        self._container.start()

        _wait_for_ready(self._container)

        # 干点清理工作吧
        def cleanup():
            try:
                container = client.containers.get(container_name)
                container.stop()
            # TODO 是不是提示一些可合适信息呀
            except docker.errors.NotFound:
                pass
            
            atexit.unregister(cleanup)

        if stop_container:
            atexit.register(cleanup)
            
        if self._container.status != "running":
            raise ValueError(f"没有成功启动 💿 镜像 {image}镜像的镜像: {self._container.logs()}")

        
        self._timeout = timeout
        self._work_dir:Path = work_dir

    @property
    def timeout(self)->int:
        return self._timeout
    
    @property
    def work_dir(self)->Path:
        return self._work_dir

    def execute_code_messages(self,code_messages:List[CodeMessage])->CodeResult:


        if len(code_messages) == 0:
            raise ValueError("没有任何可以执行的代码")
        
        outputs = []
        files = []
        last_exit_code = 0
        for code_message in code_messages:
            lang = code_message.lang
            code = code_message.content

            code_hash = md5(code.encode()).hexdigest()

            # TODO 这部分文章可能会在 prompt 做
            first_line = code.split("\n")[0]
            # 这是一个约定吧
            if first_line.startswith("# filename:"):
                filename = first_line.split(":")[1].strip()

                path = Path(filename)
                if not path.is_absolute():
                    path = Path("/workspace") / path
                path = path.resolve()
                try:
                    path.relative_to(Path("/workspace"))
                except ValueError:
                    return CodeResult(agent=None,response=None,exit_code=1, code_output="Filename is not in the workspace")
            else:
                # create a file with a automatically generated name
                filename = f"tmp_code_{code_hash}.{'py' if lang.startswith('python') else lang}"

            code_path = self._work_dir / filename
            with code_path.open("w", encoding="utf-8") as fout:
                fout.write(code)
            
            # TODO
            command = ['pip','install','pandas']
            result = self._container.exec_run(command)
            command = ["timeout", str(self._timeout), _cmd(lang), filename]

            result = self._container.exec_run(command)
            exit_code = result.exit_code
            output = result.output.decode("utf-8")
            # TODO 兼容其他信息
            if exit_code == 124:
                output += "\n"
                output += TIMEOUT_MSG

            outputs.append(output)
            files.append(code_path)

            last_exit_code = exit_code
            if exit_code != 0:
                break

        code_file = str(files[0]) if files else None
        return CodeResult(agent=None,response=None,exit_code=last_exit_code, code_output="".join(outputs), code_file=code_file)



    def restart(self) -> None:
        """(Experimental) Restart the code executor."""
        self._container.restart()
        if self._container.status != "running":
            raise ValueError(f"Failed to restart container. Logs: {self._container.logs()}")

    def stop(self) -> None:
        """(Experimental) Stop the code executor."""
        self._cleanup()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        self.stop()

    



        

        # 
            