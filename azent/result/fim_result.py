from azent.core import Result

class FIMResult(Result):
    def __init__(self, 
                 response,
                 messages,
                result_type
                 ):
        super().__init__(response)
        
    def get_data(self):
        return super().get_data()
    
    def get_message(self):
        return super().get_message()
    
    def get_text(self):
        return self.response.choices[0].text