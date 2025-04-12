import os
import threading
import asyncio
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Importiere Bot und Web-App erst nach dem Laden der Umgebungsvariablen
from bot.bot import TicketBot
from web.app import create_app

def run_flask(app):
    """Startet den Flask-Server in einem separaten Thread"""
    host = os.getenv("FLASK_HOST", "localhost")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    # Im Debug-Modus verwenden wir nicht den Threaded-Modus von Flask
    if debug:
        app.run(host=host, port=port, debug=debug)
    else:
        app.run(host=host, port=port)

def main():
    # Erstelle Bot-Instanz
    bot = TicketBot()
    
    # Erstelle Flask-App
    app = create_app(bot)
    
    # Starte Flask in separatem Thread
    flask_thread = threading.Thread(target=run_flask, args=(app,))
    flask_thread.daemon = True  # Thread wird beendet, wenn Hauptprogramm endet
    flask_thread.start()
    
    # Starte den Bot (blockiert bis zum Ende)
    bot.run()

if __name__ == "__main__":
    main()
