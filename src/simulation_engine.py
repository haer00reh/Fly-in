from config_maker import Config, hub, connection, start_hub, end_hub, drone
from pydantic import BaseModel

class simulation_engine(BaseModel):
    config: Config | None = None


    def run(self):
        pass
