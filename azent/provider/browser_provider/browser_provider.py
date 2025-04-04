from azent.core import Result


class BrowserProvider:

    def run_command(self,command):
        raise NotImplementedError()
    
    def extract_command(self,result:Result):
        raise NotImplementedError()
    