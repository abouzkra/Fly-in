from typing import Optional, Self
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class ZoneType(Enum):
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class Zone(BaseModel):
    name: str = Field(min_length=1)
    x: int
    y: int
    zone_type: ZoneType = Field(default=ZoneType.NORMAL)
    max_drones: int = Field(default=1)
    color: Optional[str] = None

    @model_validator(mode='after')
    def validate_zone(self) -> Self:
        if " " in self.name or "-" in self.name:
            raise ValueError(
                    "Zone name must not include dashes or spaces"
                    )

        if self.x < 0 or self.y < 0:
            raise ValueError(
                    "Zone coordinates must be greater or equal to 0"
                    )

        if self.max_drones <= 0:
            raise ValueError(
                    "max_drones value must be a positive integer"
                    )

        return self
