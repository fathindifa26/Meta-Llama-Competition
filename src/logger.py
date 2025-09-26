from datetime import datetime
from .config import Config

class Logger:
    def __init__(self):
        self.logs = []
        self.last_message = None
        
    def log(self, message):
        """Log a message with timestamp."""
        # Avoid duplicate consecutive messages
        if message != self.last_message:
            ts = datetime.now().strftime('%H:%M:%S')
            entry = f"{ts} - {message}"
            print(entry)
            self.logs.append(entry)
            self.last_message = message
            
            # Keep log size manageable
            if len(self.logs) > Config.MAX_LOGS:
                self.logs.pop(0)
    
    def get_logs(self):
        """Get all logged messages."""
        return self.logs 