from typing import cast
from quart import Quart, current_app

#===============
# Define a custom App class inheriting from Quart
# This allows for custom properties like the global HTTPX client
#===============
class App(Quart):
    pass

def get_app() -> App:
    #===============
    # Safely cast the current proxy object to our custom App class
    # This helps with type hinting in IDEs across the application
    #===============
    return cast(App, current_app)
