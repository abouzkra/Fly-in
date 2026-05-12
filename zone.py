from typing import Self
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class ZoneType(Enum):
    """Enum representing the type of a zone."""
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class Neighbor(BaseModel):
    """Represents a neighboring zone in the map."""
    name: str = Field(min_length=1)
    cost: float = Field(default=1.0, gt=0)
    link_capacity: int = Field(default=1, gt=0)


class Zone(BaseModel):
    """Represents a zone in the map.

    Attributes:
        name: The name of the zone.
        x: The x-coordinate of the zone.
        y: The y-coordinate of the zone.
        neighbors: A list of neighboring zones.
        zone_type: The type of the zone (normal, blocked, restricted,
            priority).
        max_drones: The maximum number of drones that can be in the zone at
            the same time.
        color: An integer representing the color of the zone for visualizer.
    """
    name: str = Field(min_length=1)
    x: int
    y: int
    neighbors: list[Neighbor] = Field(default_factory=list)
    zone_type: ZoneType = Field(default=ZoneType.NORMAL)
    max_drones: int = Field(default=1, gt=0)
    color: int

    @model_validator(mode='after')
    def validate_zone(self) -> Self:
        if " " in self.name or "-" in self.name:
            raise ValueError(
                    "Zone name must not include dashes or spaces"
                    )

        return self
