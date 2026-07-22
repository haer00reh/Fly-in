from pydantic import BaseModel

class Config(BaseModel):
    nb_drones: int
    start_hub: str
    end_hub: str
    hubs: list[str]
    connections: list[tuple[str, str]]
