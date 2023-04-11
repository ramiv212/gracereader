class Response:
    def __init__(self):
        self.response_dict = {}
        self.found_numbers = []

    def set(self,**kwargs):
        for arg in kwargs:
            self.response_dict[arg] = kwargs[arg]
    
    def get(self):
        return self.response_dict
    
    def set_total(self,found_number):
        self.found_numbers.append(found_number)

    def get_total(self):
        if self.found_numbers:
            return max(self.found_numbers)
    
    def print(self):
        print(self.response_dict)