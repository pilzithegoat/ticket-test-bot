import discord
from discord import app_commands

def register_commands(bot_instance):
    """Registriert alle Slash-Commands für den Bot"""
    
    @bot_instance.bot.tree.command(name="setup", description="Richtet das Ticket-System ein")
    @app_commands.default_permissions(administrator=True)
    async def setup(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Du benötigst Administrator-Berechtigungen, um diesen Befehl zu verwenden!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild_id)
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
        
        await interaction.response.send_message("Erstelle Ticket-Panel...", ephemeral=True)
        channel = interaction.channel
        message = await channel.send(embed=embed, view=view)
        
        # Speichere Ticket-Kanal ID
        bot_instance.config_manager.set_ticket_channel(guild_id, str(channel.id))
        
        await interaction.edit_original_response(content="Ticket-Panel erfolgreich erstellt!")
    
    @bot_instance.bot.tree.command(name="set_log_channel", description="Legt den Kanal für Ticket-Logs fest")
    @app_commands.default_permissions(administrator=True)
    async def set_log_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Du benötigst Administrator-Berechtigungen, um diesen Befehl zu verwenden!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild_id)
        bot_instance.config_manager.set_log_channel(guild_id, str(channel.id))
        
        await interaction.response.send_message(f"Log-Kanal auf {channel.mention} gesetzt", ephemeral=True)
    
    @bot_instance.bot.tree.command(name="add_admin_role", description="Fügt eine Rolle hinzu, die alle Tickets verwalten kann")
    @app_commands.default_permissions(administrator=True)
    async def add_admin_role(interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Du benötigst Administrator-Berechtigungen, um diesen Befehl zu verwenden!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild_id)
        guild_config = bot_instance.config_manager.get_guild_config(guild_id)
        
        role_id = str(role.id)
        if role_id not in guild_config["admin_role_ids"]:
            admin_roles = guild_config["admin_role_ids"] + [role_id]
            bot_instance.config_manager.update_guild_admin_roles(guild_id, admin_roles)
            await interaction.response.send_message(f"{role.mention} wurde als Admin-Rolle hinzugefügt", ephemeral=True)
        else:
            await interaction.response.send_message(f"{role.mention} ist bereits eine Admin-Rolle", ephemeral=True)
