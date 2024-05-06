class MessageManager:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    
    @staticmethod
    def warning(message:str):
        print(MessageManager.WARNING, message, MessageManager.ENDC)
    
    @staticmethod
    def ok(message:str):
        print(MessageManager.OKGREEN, message, MessageManager.ENDC)
    
    @staticmethod
    def error(message:str):
        raise NotImplementedError()

