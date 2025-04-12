import os
from flask import Flask, redirect, url_for, render_template, request, jsonify, session
from typing import Dict, Any

from web.auth import setup_oauth
from utils.logger import Logger

def create_app(bot_instance):
    """Erstellt die Flask-App für das Web-Interface"""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web/static'))
    
    # Logger
    logger = Logger("web_app")
    
    # Konfiguriere Flask
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    
    # Konfiguriere Discord OAuth2
    discord_oauth = setup_oauth(app)
    
    @app.route("/")
    def home():
        if not discord_oauth.authorized:
            return render_template("login.html")
        return redirect(url_for("dashboard"))
    
    @app.route("/login")
    def login():
        return discord_oauth.create_session()
    
    @app.route("/callback")
    def callback():
        discord_oauth.callback()
        return redirect(url_for("dashboard"))
    
    @app.route("/dashboard")
    @discord_oauth.requires_authorization
    def dashboard():
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Filtere nur Server, auf denen der Bot ist und der Benutzer manage_guild hat
        bot_guilds = []
        for guild in guilds:
            if guild.permissions.administrator or guild.permissions.manage_guild:
                bot_guilds.append({
                    "id": guild.id,
                    "name": guild.name,
                    "icon": guild.icon_url if guild.icon_url else None
                })
        
        return render_template("dashboard.html", user=user, guilds=bot_guilds)
    
    @app.route("/guild/<guild_id>")
    @discord_oauth.requires_authorization
    def guild_settings(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe, ob der Benutzer Berechtigungen für diesen Server hat
        has_permission = False
        guild_name = ""
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                    guild_name = guild.name
                break
        
        if not has_permission:
            return redirect(url_for("dashboard"))
        
        guild_config = bot_instance.config_manager.get_guild_config(guild_id)
        
        return render_template(
            "guild_settings.html", 
            user=user, 
            guild_id=guild_id,
            guild_name=guild_name,
            config=guild_config
        )
    
    @app.route("/api/guild/<guild_id>/categories", methods=["POST"])
    @discord_oauth.requires_authorization
    def update_categories(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe Berechtigungen
        has_permission = False
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                break
        
        if not has_permission:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Aktualisiere Kategorien
        categories = request.json.get("categories", [])
        bot_instance.config_manager.update_guild_categories(guild_id, categories)
        
        return jsonify({"success": True})
    
    @app.route("/api/guild/<guild_id>/admin-roles", methods=["POST"])
    @discord_oauth.requires_authorization
    def update_admin_roles(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe Berechtigungen
        has_permission = False
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                break
        
        if not has_permission:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Aktualisiere Admin-Rollen
        admin_roles = request.json.get("admin_roles", [])
        bot_instance.config_manager.update_guild_admin_roles(guild_id, admin_roles)
        
        return jsonify({"success": True})
    
    @app.route("/api/guild/<guild_id>/log-channel", methods=["POST"])
    @discord_oauth.requires_authorization
    def update_log_channel(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe Berechtigungen
        has_permission = False
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                break
        
        if not has_permission:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Aktualisiere Log-Kanal
        channel_id = request.json.get("channel_id")
        bot_instance.config_manager.set_log_channel(guild_id, channel_id)
        
        return jsonify({"success": True})
    
    @app.route("/api/guild/<guild_id>/channels", methods=["GET"])
    @discord_oauth.requires_authorization
    def get_guild_channels(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe Berechtigungen
        has_permission = False
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                break
        
        if not has_permission:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Hole Guild-Objekt vom Bot
        guild = bot_instance.bot.get_guild(int(guild_id))
        if not guild:
            return jsonify({"error": "Guild not found"}), 404
        
        # Sammle alle Text-Kanäle
        channels = []
        for channel in guild.text_channels:
            channels.append({
                "id": str(channel.id),
                "name": channel.name,
                "category": channel.category.name if channel.category else "Keine Kategorie"
            })
        
        return jsonify({"channels": channels})
    
    @app.route("/api/guild/<guild_id>/roles", methods=["GET"])
    @discord_oauth.requires_authorization
    def get_guild_roles(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe Berechtigungen
        has_permission = False
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                break
        
        if not has_permission:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Hole Guild-Objekt vom Bot
        guild = bot_instance.bot.get_guild(int(guild_id))
        if not guild:
            return jsonify({"error": "Guild not found"}), 404
        
        # Sammle alle Rollen (außer @everyone)
        roles = []
        for role in guild.roles:
            if role.name != "@everyone":
                roles.append({
                    "id": str(role.id),
                    "name": role.name,
                    "color": role.color.value
                })
        
        return jsonify({"roles": roles})
    
    @app.route("/api/guild/<guild_id>/tickets", methods=["GET"])
    @discord_oauth.requires_authorization
    def get_guild_tickets(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe Berechtigungen
        has_permission = False
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                break
        
        if not has_permission:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Hole Tickets aus Config
        guild_config = bot_instance.config_manager.get_guild_config(guild_id)
        tickets = guild_config.get("tickets", {})
        
        return jsonify({"tickets": tickets})
    
    @app.route("/api/guild/<guild_id>/ticket-settings", methods=["POST"])
    @discord_oauth.requires_authorization
    def create_ticket_panel(guild_id):
        user = discord_oauth.fetch_user()
        guilds = discord_oauth.fetch_guilds()
        
        # Prüfe Berechtigungen
        has_permission = False
        for guild in guilds:
            if str(guild.id) == guild_id:
                if guild.permissions.administrator or guild.permissions.manage_guild:
                    has_permission = True
                break
        
        if not has_permission:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Hole Daten aus Request
        data = request.json
        channel_id = data.get("channel_id")
        
        # Setze Ticket-Kanal
        bot_instance.config_manager.set_ticket_channel(guild_id, channel_id)
        
        # Erstelle das Panel in Discord (asynchron)
        async def create_panel():
            guild = bot_instance.bot.get_guild(int(guild_id))
            if not guild:
                return
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return
            
            guild_config = bot_instance.config_manager.get_guild_config(guild_id)
            
            # Erstelle Ticket-Panel Embed
            embed = discord.Embed(
                title="Support Ticket System",
                description="Klicke auf einen der unten stehenden Buttons, um ein Support-Ticket zu erstellen",
                color=discord.Color.blue()
            )
            
            # Erstelle Buttons für jede Ticket-Kategorie
            view = discord.ui.View(timeout=None)
            
            for category in guild_config["ticket_categories"]:
                button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label=category["name"],
                    custom_id=f"create_ticket:{category['name']}"
                )
                view.add_item(button)
            
            await channel.send(embed=embed, view=view)
        
        # Führe den asynchronen Code aus
        bot_instance.bot.loop.create_task(create_panel())
        
        return jsonify({"success": True})
    
    @app.route("/logout")
    def logout():
        discord_oauth.logout()
        return redirect(url_for("home"))
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404
    
    return app
