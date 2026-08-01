from config_maker import Config, hub, connection, start_hub, end_hub, drone
from parser import Parser
from pathlib import Path
import pygame
from pydantic import BaseModel

class graph_visualizer(BaseModel):
    config: Config | None = None

    def run(self):
        pass
