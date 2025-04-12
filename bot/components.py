import discord

def register_component_callbacks(bot_instance):
    """Registriert alle Component-Callbacks für den Bot"""
    
    @bot_instance.bot.event
    async def on_interaction(interaction: discord.Interaction):
        """Event für Button-Interaktionen und andere Components"""
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            
            # Ticket erstellen
            if custom_id.startswith("create_ticket:"):
                category = custom_id.split(":")[1]
                await bot_instance.create_ticket(interaction, category)
            
            # Ticket schließen
            elif custom_id == "close_ticket":
                await bot_instance.close_ticket(interaction)
