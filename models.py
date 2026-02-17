from enum import Enum
from typing import Self
from pydantic import BaseModel, Field, model_validator


class Map(BaseModel):
    nb_drones: int
    zones: dict[str, Zone]
