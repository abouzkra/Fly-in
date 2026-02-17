import re
from typing import Dict, Set, Tuple, Optional

from models import Zone, Connection, ZoneType
from errors import ParsingError


def parse_metadata(raw: str, line_number: int) -> dict:
    """
    Parse metadata blocks like:
    [zone=restricted color=blue max_drones=8]
    """

    # ----------------------------
    if not raw:
        return {}

    raw = raw.strip()

    if not (raw.startswith("[") and raw.endswith("]")):
        raise ParsingError(line_number, "invalid metadata syntax (missing brackets)")

    content = raw[1:-1].strip()
    if not content:
        return {}

    metadata = {}

    parts = content.split()
    for part in parts:
        if "=" not in part:
            raise ParsingError(line_number, f"invalid metadata entry '{part}'")

        key, value = part.split("=", 1)
        metadata[key] = value

    return metadata


class MapParser:
    def __init__(self):
        self.nb_drones: Optional[int] = None

        self.zones: Dict[str, Zone] = {}
        self.connections: Set[Tuple[str, str]] = set()

        self.start_zone: Optional[str] = None
        self.end_zone: Optional[str] = None

    def parse_file(self, filepath: str):
        with open(filepath, "r") as f:
            for line_number, raw_line in enumerate(f, start=1):
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                if self.nb_drones is None:
                    self._parse_nb_drones(line, line_number)
                    continue

                if line.startswith("hub:"):
                    self._parse_zone(line, line_number, zone_kind="hub")

                elif line.startswith("start_hub:"):
                    self._parse_zone(line, line_number, zone_kind="start")

                elif line.startswith("end_hub:"):
                    self._parse_zone(line, line_number, zone_kind="end")

                elif line.startswith("connection:"):
                    self._parse_connection(line, line_number)

                else:
                    raise ParsingError(line_number, f"unknown line format: '{line}'")

        # Final validation
        self._final_checks()

        return self

    def _parse_nb_drones(self, line: str, line_number: int):
        match = re.match(r"nb_drones:\s*(\d+)$", line)
        if not match:
            raise ParsingError(
                line_number,
                "first line must be 'nb_drones: <positive_integer>'"
            )

        self.nb_drones = int(match.group(1))

        if self.nb_drones <= 0:
            raise ParsingError(line_number, "nb_drones must be positive")

    def _parse_zone(self, line: str, line_number: int, zone_kind: str):
        """
        Example:
        hub: maze_a1 1 0 [color=blue]
        start_hub: start 0 0 [color=green max_drones=8]
        """

        # Split metadata
        metadata_part = ""
        if "[" in line:
            line, metadata_part = line.split("[", 1)
            metadata_part = "[" + metadata_part

        tokens = line.split()

        if len(tokens) != 4:
            raise ParsingError(line_number, "invalid zone definition format")

        _, name, x, y = tokens

        if name in self.zones:
            raise ParsingError(line_number, f"duplicate zone name '{name}'")

        metadata = parse_metadata(metadata_part, line_number)

        # Zone type check
        zone_type = metadata.get("zone", "normal")
        try:
            zone_type = ZoneType(zone_type)
        except ValueError:
            raise ParsingError(line_number, f"invalid zone type '{zone_type}'")

        # Build Zone with Pydantic validation
        try:
            zone = Zone(
                name=name,
                x=int(x),
                y=int(y),
                zone_type=zone_type,
                color=metadata.get("color"),
                max_drones=int(metadata["max_drones"])
                if "max_drones" in metadata
                else None,
            )
        except Exception as e:
            raise ParsingError(line_number, str(e))

        # Store zone
        self.zones[name] = zone

        # Track start/end
        if zone_kind == "start":
            if self.start_zone is not None:
                raise ParsingError(line_number, "multiple start_hub definitions found")
            self.start_zone = name

        elif zone_kind == "end":
            if self.end_zone is not None:
                raise ParsingError(line_number, "multiple end_hub definitions found")
            self.end_zone = name

    def _parse_connection(self, line: str, line_number: int):
        """
        Example:
        connection: maze_a1-maze_a2 [max_link_capacity=3]
        """

        metadata_part = ""
        if "[" in line:
            line, metadata_part = line.split("[", 1)
            metadata_part = "[" + metadata_part

        match = re.match(r"connection:\s*([^-]+)-([^\s]+)", line)
        if not match:
            raise ParsingError(line_number, "invalid connection syntax")

        zone1, zone2 = match.group(1), match.group(2)

        # Zones must exist
        if zone1 not in self.zones:
            raise ParsingError(line_number, f"undefined zone '{zone1}'")

        if zone2 not in self.zones:
            raise ParsingError(line_number, f"undefined zone '{zone2}'")

        # Duplicate detection (a-b == b-a)
        edge = tuple(sorted((zone1, zone2)))

        if edge in self.connections:
            raise ParsingError(line_number, f"duplicate connection '{zone1}-{zone2}'")

        metadata = parse_metadata(metadata_part, line_number)

        # Validate connection with Pydantic
        try:
            conn = Connection(
                zone1=zone1,
                zone2=zone2,
                max_link_capacity=int(metadata["max_link_capacity"])
                if "max_link_capacity" in metadata
                else None,
            )
        except Exception as e:
            raise ParsingError(line_number, str(e))

        self.connections.add(edge)

    def _final_checks(self):
        if self.start_zone is None:
            raise ParsingError(-1, "missing start_hub definition")

        if self.end_zone is None:
            raise ParsingError(-1, "missing end_hub definition")

