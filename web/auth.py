import os
import requests
from functools import wraps
from flask import session, redirect, request, url_for
from urllib.parse import urlencode
from dataclasses import dataclass
from typing import List, Optional

DISCORD_API = "https://discord.com/api"

@dataclass
class DiscordUser:
    id: str
    username: str
    discriminator: str
    avatar: Optional[str] = None
    
    @property
    def avatar_url(self) -> Optional[str]:
        if self.avatar:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        return None

@dataclass
class DiscordGuildPermissions:
    value: int
    
    @property
    def administrator(self) -> bool:
        return (self.value & 0x8) == 0x8
    
    @property
    def manage_guild(self) -> bool:
        return (self.value & 0x20) == 0x20

@dataclass
class DiscordGuild:
    id: str
    name: str
    icon: Optional[str] = None
    owner: bool = False
    permissions: Optional[DiscordGuildPermissions] = None
    
    @property
    def icon_url(self) -> Optional[str]:
        if self.icon:
            return f"https://cdn.discordapp.com/icons/{self.id}/{self.icon}.png"
        return None

class DiscordOAuth2:
    def __init__(self, app, client_id, client_secret, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.token_url = f"{DISCORD_API}/oauth2/token"
        self.authorized = False
        
        @app.before_request
        def check_authorization():
            self.authorized = "discord_token" in session
    
    def create_session(self):
        """Erstellt eine OAuth2-Sitzung mit Discord"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scope
        }
        url = f"{DISCORD_API}/oauth2/authorize?{urlencode(params)}"
        return redirect(url)
    
    def callback(self):
        """Verarbeitet den Callback von Discord"""
        code = request.args.get("code")
        if not code:
            return False
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope
        }
        
        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            session["discord_token"] = token_data
            self.authorized = True
            return True
        return False
    
    def logout(self):
        """Beendet die Sitzung"""
        if "discord_token" in session:
            del session["discord_token"]
        self.authorized = False
    
    def get_token(self):
        """Gibt das aktuelle Token zurück"""
        token_data = session.get("discord_token")
        if not token_data:
            return None
        
        # Prüfen, ob Token aktualisiert werden muss
        if "expires_at" in token_data and token_data["expires_at"] < time.time():
            # Token aktualisieren
            refresh_token = token_data.get("refresh_token")
            if refresh_token:
                data = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
                
                response = requests.post(self.token_url, data=data)
                if response.status_code == 200:
                    token_data = response.json()
                    token_data["expires_at"] = time.time() + token_data["expires_in"]
                    session["discord_token"] = token_data
                else:
                    # Bei Fehler: Token entfernen und neu anmelden lassen
                    del session["discord_token"]
                    self.authorized = False
                    return None
        
        return token_data.get("access_token")
    
    def fetch_user(self) -> Optional[DiscordUser]:
        """Holt Benutzerinformationen von Discord"""
        token = self.get_token()
        if not token:
            return None
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{DISCORD_API}/users/@me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return DiscordUser(
                id=data["id"],
                username=data["username"],
                discriminator=data.get("discriminator", "0"),
                avatar=data.get("avatar")
            )
        return None
    
    def fetch_guilds(self) -> List[DiscordGuild]:
        """Holt die Server des Benutzers von Discord"""
        token = self.get_token()
        if not token:
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{DISCORD_API}/users/@me/guilds", headers=headers)
        
        if response.status_code == 200:
            guilds = []
            for guild_data in response.json():
                guilds.append(DiscordGuild(
                    id=guild_data["id"],
                    name=guild_data["name"],
                    icon=guild_data.get("icon"),
                    owner=guild_data.get("owner", False),
                    permissions=DiscordGuildPermissions(int(guild_data.get("permissions", 0)))
                ))
            return guilds
        return []
    
    def requires_authorization(self, f):
        """Decorator für Routen, die Autorisierung erfordern"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.authorized:
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function

def setup_oauth(app):
    """Konfiguriert OAuth2 für die Flask-App"""
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    redirect_uri = os.getenv("OAUTH2_REDIRECT_URI")
    
    oauth = DiscordOAuth2(
        app=app,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="identify guilds"
    )
    
    return oauth

# Für Token-Expiry
import time
