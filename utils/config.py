import os
import json
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Verwaltet die Konfiguration des Bots und der Server
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "config.json")
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Lädt die Konfiguration aus der Datei oder erstellt eine neue"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            default_config = {
                "guilds": {}
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Speichert die Konfiguration in der Datei"""
        if config is None:
            config = self.config
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    
    def get_guild_config(self, guild_id: str) -> Dict[str, Any]:
        """Gibt die Konfiguration für einen Server zurück oder erstellt eine neue"""
        if guild_id not in self.config["guilds"]:
            self.config["guilds"][guild_id] = {
                "ticket_categories": [
                    {
                        "name": "Support",
                        "description": "Hilfe vom Support-Team erhalten",
                        "color": 3447003,
                        "role_ids": []
                    }
                ],
                "admin_role_ids": [],
                "ticket_channel_id": None,
                "ticket_log_channel_id": None,
                "tickets": {}
            }
            self.save_config()
        
        return self.config["guilds"][guild_id]
    
    def update_guild_categories(self, guild_id: str, categories: list) -> None:
        """Aktualisiert die Ticket-Kategorien eines Servers"""
        self.config["guilds"][guild_id]["ticket_categories"] = categories
        self.save_config()
    
    def update_guild_admin_roles(self, guild_id: str, role_ids: list) -> None:
        """Aktualisiert die Admin-Rollen eines Servers"""
        self.config["guilds"][guild_id]["admin_role_ids"] = role_ids
        self.save_config()
    
    def update_ticket_status(self, guild_id: str, ticket_id: str, status: str, closed_at: str = None) -> None:
        """Aktualisiert den Status eines Tickets"""
        self.config["guilds"][guild_id]["tickets"][ticket_id]["status"] = status
        if closed_at:
            self.config["guilds"][guild_id]["tickets"][ticket_id]["closed_at"] = closed_at
        self.save_config()
    
    def add_ticket(self, guild_id: str, ticket_id: str, user_id: str, channel_id: str, category: str) -> None:
        """Fügt ein neues Ticket hinzu"""
        self.config["guilds"][guild_id]["tickets"][ticket_id] = {
            "user_id": user_id,
            "channel_id": channel_id,
            "category": category,
            "status": "open",
            "created_at": datetime.datetime.now().isoformat(),
            "closed_at": None
        }
        self.save_config()
    
    def set_log_channel(self, guild_id: str, channel_id: str) -> None:
        """Setzt den Log-Kanal für einen Server"""
        self.config["guilds"][guild_id]["ticket_log_channel_id"] = channel_id
        self.save_config()
    
    def set_ticket_channel(self, guild_id: str, channel_id: str) -> None:
        """Setzt den Kanal für das Ticket-Panel"""
        self.config["guilds"][guild_id]["ticket_channel_id"] = channel_id
        self.save_config()

# Datetime-Import für add_ticket
import datetime
