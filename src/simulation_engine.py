from config_maker import Config
from pydantic import BaseModel

class simulation_engine(BaseModel):
    config: Config | None = None


    def run(self):
        pass

    def path_finder(self):
        pass

    def turn_scheduler(self):
        pass
