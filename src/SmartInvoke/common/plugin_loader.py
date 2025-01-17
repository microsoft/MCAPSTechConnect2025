import importlib  

class PluginLoader:  
    @staticmethod  
    def load_class(module_name, class_name):  
        module = importlib.import_module(module_name)  
        return getattr(module, class_name) 