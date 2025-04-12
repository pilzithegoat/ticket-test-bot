import logging
import os
from datetime import datetime

class Logger:
    """
    Logger für den Bot und die Website
    """
    def __init__(self, name: str, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.name = name
        
        # Erstelle Log-Verzeichnis, falls es nicht existiert
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Erstelle Logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Dateiname mit Datum
        log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        # Handler für Datei
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Handler für Konsole
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Handler hinzufügen
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Info-Log"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Warnung-Log"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Fehler-Log"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Debug-Log"""
        self.logger.debug(message)
