import threading
from web import run_flask
from bot import run_bot

if __name__ == "__main__":
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # Ensure it exits when the main program exits
    flask_thread.start()

    # Run the Discord bot
    run_bot()