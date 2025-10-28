import os


class Config:
    class App:
        NAME = "solver-controller"
        VERSION = "0.1.0"
        DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    class Api:
        TITLE = "Solver Controller API"
        DESCRIPTION = "Manages solver and instances"
        VERSION = "v1"
        ROOT_PATH = "/"
