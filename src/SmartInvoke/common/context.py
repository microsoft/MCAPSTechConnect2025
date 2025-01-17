class Context:  
    def __init__(self):  
        self.data = {}  
    def set(self, key, value):  
        self.data[key] = value  
    def get(self, key):  
        if self.data.keys() is None or key not in self.data.keys():  
            return ""  
        return self.data.get(key)  
    def __iter__(self):  
        return iter(self.data.items())  