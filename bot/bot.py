import os
import discord
from discord.ext import commands
import asyncio
from typing import Optional
import datetime

from utils.config import ConfigManager
from utils.logger import Logger
from bot.commands import register_commands
from bot.components import register_component_callbacks

class TicketBot:
    """
    Hauptklasse für den Discord Ticket Bot
    """
    def __init__(self):
        self.token = os.getenv("BOT_TOKEN")
        self.config_manager = ConfigManager()
        self.logger = Logger("ticket_bot")
        
        # Erstelle Bot mit Intents
        intents = discord.Intents.default()
        intents.messages = True
        intents.guilds = True
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # Registriere Events
        self.bot.event(self.on_ready)
        self.bot.event(self.on_interaction)
        
        # Registriere Commands und Component-Callbacks
        register_commands(self)
        register_component_callbacks(self)
    
    async def on_ready(self):
        """Event, wenn der Bot bereit ist"""
        self.logger.info(f'Logged in as {self.bot.user.name}')
        try:
            synced = await self.bot.tree.sync()
            self.logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            self.logger.error(f"Error syncing commands: {e}")
    
    async def on_interaction(self, interaction: discord.Interaction):
        """Event für Button-Interaktionen und andere Components"""
        if interaction.type == discord.InteractionType.component:
            # Die Logik für Component-Interaktionen ist in components.py
            pass
    
    async def create_ticket(self, interaction: discord.Interaction, category: str):
        """Erstellt ein neues Ticket"""
        guild_id = str(interaction.guild_id)
        guild_config = self.config_manager.get_guild_config(guild_id)
        user_id = str(interaction.user.id)
        
        # Prüfe, ob der Benutzer bereits ein offenes Ticket hat
        for ticket_id, ticket_info in guild_config["tickets"].items():
            if ticket_info["user_id"] == user_id and ticket_info["status"] == "open":
                await interaction.response.send_message("Du hast bereits ein offenes Ticket!", ephemeral=True)
                return
        
        guild = interaction.guild
        
        # Finde oder erstelle Tickets-Kategorie
        category_channel = discord.utils.get(guild.categories, name="Tickets")
        if not category_channel:
            category_channel = await guild.create_category("Tickets")
        
        # Erstelle Ticket-Kanal
        ticket_count = len(guild_config["tickets"]) + 1
        ticket_name = f"ticket-{ticket_count}-{interaction.user.name.lower()}"
        
        # Setze Berechtigungen
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        # Füge Rollenberechtigungen hinzu
        for cat in guild_config["ticket_categories"]:
            if cat["name"] == category:
                for role_id in cat["role_ids"]:
                    role = guild.get_role(int(role_id))
                    if role:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        for role_id in guild_config["admin_role_ids"]:
            role = guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        # Erstelle den Kanal
        ticket_channel = await guild.create_text_channel(
            name=ticket_name,
            category=category_channel,
            overwrites=overwrites,
            topic=f"Ticket für {interaction.user.name} - {category}"
        )
        
        # Erstelle Embed für das Ticket
        embed = discord.Embed(
            title=f"Ticket: {category}",
            description=f"Danke für die Erstellung eines Tickets, {interaction.user.mention}. Das Support-Team wird sich in Kürze bei dir melden.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=f"Ticket ID: {ticket_count}")
        
        # Erstelle Buttons
        close_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Ticket schließen", custom_id="close_ticket")
        
        view = discord.ui.View()
        view.add_item(close_button)
        
        message = await ticket_channel.send(embed=embed, view=view)
        await message.pin()
        
        # Speichere Ticket-Infos
        ticket_id = str(ticket_count)
        self.config_manager.add_ticket(
            guild_id=guild_id,
            ticket_id=ticket_id,
            user_id=user_id,
            channel_id=str(ticket_channel.id),
            category=category
        )
        
        # Antworte auf Interaktion
        await interaction.response.send_message(f"Ticket erstellt! Gehe zu {ticket_channel.mention}", ephemeral=True)
        
        # Logge Ticket-Erstellung
        log_channel_id = guild_config.get("ticket_log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                log_embed = discord.Embed(
                    title="Ticket erstellt",
                    description=f"Ticket #{ticket_id} wurde von {interaction.user.mention} erstellt",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                log_embed.add_field(name="Kategorie", value=category)
                log_embed.add_field(name="Kanal", value=ticket_channel.mention)
                await log_channel.send(embed=log_embed)
    
    async def close_ticket(self, interaction: discord.Interaction):
        """Schließt ein Ticket"""
        guild_id = str(interaction.guild_id)
        guild_config = self.config_manager.get_guild_config(guild_id)
        channel_id = str(interaction.channel_id)
        
        # Finde das Ticket
        ticket_id = None
        for t_id, ticket in guild_config["tickets"].items():
            if ticket["channel_id"] == channel_id and ticket["status"] == "open":
                ticket_id = t_id
                break
        
        if ticket_id:
            # Aktualisiere Ticket-Status
            self.config_manager.update_ticket_status(
                guild_id=guild_id,
                ticket_id=ticket_id,
                status="closed",
                closed_at=datetime.datetime.now().isoformat()
            )
            
            # Erstelle Transkript
            await self.create_transcript(interaction, ticket_id, guild_config)
            
            # Antworte auf Interaktion
            await interaction.response.send_message("Ticket wird in 5 Sekunden geschlossen...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("Konnte kein offenes Ticket für diesen Kanal finden.", ephemeral=True)
    
    async def create_transcript(self, interaction: discord.Interaction, ticket_id: str, guild_config: dict):
        """Erstellt ein Transkript des Tickets und sendet es an den Log-Kanal"""
        # Sammle Nachrichten
        messages = []
        async for msg in interaction.channel.history(limit=100, oldest_first=True):
            time = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            content = msg.content if msg.content else "*[Kein Textinhalt]*"
            messages.append(f"[{time}] {msg.author.name}: {content}")
        
        transcript = "\n".join(messages)
        
        # Erstelle Transkript-Datei
        transcript_dir = "data/transcripts"
        if not os.path.exists(transcript_dir):
            os.makedirs(transcript_dir)
        
        file_path = f'{transcript_dir}/ticket-{ticket_id}.txt'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        # Sende Transkript an Log-Kanal
        log_channel_id = guild_config.get("ticket_log_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                user = await self.bot.fetch_user(int(guild_config["tickets"][ticket_id]["user_id"]))
                
                log_embed = discord.Embed(
                    title="Ticket geschlossen",
                    description=f"Ticket #{ticket_id} wurde von {interaction.user.mention} geschlossen",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.now()
                )
                log_embed.add_field(name="Erstellt von", value=user.mention if user else "Unbekannt")
                log_embed.add_field(name="Kategorie", value=guild_config["tickets"][ticket_id]["category"])
                
                with open(file_path, 'rb') as f:
                    transcript_file = discord.File(f, filename=f'ticket-{ticket_id}.txt')
                    await log_channel.send(embed=log_embed, file=transcript_file)
    
    def run(self):
        """Startet den Bot"""
        self.logger.info("Starting bot...")
        self.bot.run(self.token)
