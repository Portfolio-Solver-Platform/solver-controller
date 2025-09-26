import os


class Config:
    class Flask:
        HOST = "127.0.0.1"
        PORT = 5000
        DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    class App:
        NAME = "solver-controller"
        VERSION = "0.1.0"

    class Api:
        VERSION = "v1"

