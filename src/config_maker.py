from pydantic import BaseModel


class hub(BaseModel):
    name: str
    x: int
    y: int
    color: str
    zone_type: str
    max_drones: int


class connection(BaseModel):
    hub1: hub
    hub2: hub
    max_link: int


class end_hub(hub):
    pass


class start_hub(hub):
    pass


class drone(BaseModel):
    id: int
    start_hub: hub
    end_hub: hub



class Config(BaseModel):
    nb_drones: int
    start: start_hub
    end: end_hub
    hubs: list[hub]
    connections: list[connection]
    config_table: list[str] = []
    def __init__(self):
        pass

