from typing import cast
from quart import Quart, current_app

class App(Quart):
    pass

def get_app() -> App:
    return cast(App, current_app)
