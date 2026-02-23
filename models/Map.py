from typing import Any
from .Error import ParsingError
from .Zone import Zone, ZoneType, Neighbor

# TODO: Add zone coordinate validation (check zone coordinates after normalization against zone range)
# TODO: Check duplicate key-value pairs in metadata

class Map:
    def __init__(self):
        self.nb_drones: int | None = None
        self.start_zone: str | None = None
        self.end_zone: str | None = None
        self.zones: dict[str, Zone] = {}
        self.connections: list[tuple[str, str]] = list()

    def parse_file(self, input_file: str) -> None:
        with open(input_file, 'r') as file:
            for line_nb, line in enumerate(file, start=1):
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if self.nb_drones is None:
                    self._parse_nb_drones(line, line_nb)
                    continue

                if line.startswith('start_hub:'):
                    self._parse_zone(line, line_nb, 'start')
                elif line.startswith('end_hub:'):
                    self._parse_zone(line, line_nb, 'end')
                elif line.startswith('hub:'):
                    self._parse_zone(line, line_nb, 'hub')
                elif line.startswith('connection:'):
                    self._parse_connection(line, line_nb)
                else:
                    raise ParsingError(
                        line_nb,
                        f"Invalid line format: \"{line}\""
                        )

            if self.start_zone is None:
                raise ParsingError(-1, "Missing start_hub definition")
            if self.end_zone is None:
                raise ParsingError(-1, "Missing end_hub definition")


    def _parse_nb_drones(self, line: str, line_nb: int) -> None:
        if line.startswith('nb_drones:'):
            try:
                self.nb_drones = int(line.split(':', 1)[1].strip())
            except Exception as e:
                raise ParsingError(line_nb, str(e))
        else:
            raise ParsingError(
                line_nb,
                "Input file must start with: " +
                "\"nb_drones': <positive_integer>\""
                )

        if self.nb_drones <= 0:
            raise ParsingError(
                line_nb,
                "nb_drones must be a positive integer"
                )

    def _parse_zone(self, line: str, line_nb: int, zone_kind: str):
        metadata = ""

        if "[" in line:
            line, metadata = line.split('[', 1)
            metadata = "[" + metadata

        tokens = line.split()
        if len(tokens) != 4:
            raise ParsingError(
                line_nb,
                "Invalid zone definition format, syntax:\n" +
                "\t\"<zone_kind>: <name> <x> <y> [metadata]\""
                )

        _, name, x, y = tokens

        metadata = self._parse_metadata(
                metadata, line_nb,
                {'zone', 'color', 'max_drones'}
                )

        if name in self.zones:
            raise ParsingError(line_nb, f"Duplicate zone name: '{name}'")

        zone_type = metadata.get("zone", "normal")
        try:
            zone_type = ZoneType(zone_type)
        except ValueError:
            raise ParsingError(line_nb, f"Invalid zone type: '{zone_type}'")

        try:
            zone = Zone(
                    name=name,
                    x=x, y=y,
                    zone_type=zone_type,
                    max_drones=metadata.get('max_drones', 1),
                    color=metadata.get('color')
                    )
        except Exception as e:
            raise ParsingError(line_nb, str(e))

        if (zone.x, zone.y) in [(z.x, z.y) for z in self.zones.values()]:
            raise ParsingError(
                line_nb,
                "Zones with duplicate coordinates were found" + 
                f"{(zone.x, zone.y)}" +
                f"{[(z.x, z.y) for z in self.zones.values()]}"
                )

        if zone_kind == 'start':
            if self.start_zone:
                raise ParsingError(
                    line_nb,
                    "Found multiple start_hub definitions"
                    )
            self.start_zone = name

        if zone_kind == 'end':
            if self.end_zone:
                raise ParsingError(
                    line_nb,
                    "Found multiple end_hub definitions"
                    )
            self.end_zone = name

        self.zones[name] = zone

    def _parse_connection(self, line: str, line_nb: int):
        if not line.startswith("connection:") or '-' not in line:
            raise ParsingError(
                line_nb,
                "Invalid connection definition, syntax:\n"
                "\t\"connection: <zone1>-<zone2> [metadata]\""
                )

        raw_md = ""
        if "[" in line:
            line, raw_md = line.split('[', 1)
            raw_md = "[" + raw_md

        line = line[len("connection:"):].strip()

        zone1, zone2 = line.split('-', 1)
        if not zone1 or not zone2:
            raise ParsingError(
                line_nb,
                "Invalid connection format (missing zone name)"
                )

        if zone1 == zone2:
            raise ParsingError(
                line_nb,
                "Connection names are the same"
                )

        if zone1 not in self.zones:
            raise ParsingError(
                line_nb,
                f"Undefined zone: '{zone1}'"
                )
        if zone2 not in self.zones:
            raise ParsingError(
                line_nb,
                f"Undefined zone: '{zone2}'"
                )

        edge = tuple(sorted((zone1, zone2)))

        if edge in self.connections:
            raise ParsingError(
                line_nb,
                f"Duplicate connection: '{zone1}-{zone2}'"
                )

        self.connections.append(edge)

        metadata = {}
        if raw_md:
            metadata = self._parse_metadata(
                    raw_md, line_nb, {'max_link_capacity'}
                    )
        try:
            cap = int(metadata.get('max_link_capacity', 1))
            if cap <= 0:
                raise ValueError
        except ValueError:
            raise ParsingError(
                line_nb,
                "max_link_capacity must be a positive integer"
                )

        self.zones[zone1].neighbors.append(
                Neighbor(name=zone2, link_capacity=cap)
                )
        self.zones[zone2].neighbors.append(
                Neighbor(name=zone1, link_capacity=cap)
                )

    def _parse_metadata(
            self,
            raw_md: str,
            line_nb: int,
            md_keys: set[str]
            ) -> dict[str, Any]:
        raw_md = raw_md.strip()

        if not raw_md.startswith('[') or not raw_md.endswith(']'):
            raise ParsingError(
                line_nb,
                "Invalid metadata syntax (missing brackets)"
                )

        raw_md = raw_md[1: -1]

        if not raw_md:
            return {}

        metadata = {}

        for pair in raw_md.split():
            if '=' not in pair:
                raise ParsingError(
                    line_nb,
                    f"Invalid metadata entry: '{pair}'"
                    )

            k, v = pair.split('=', 1)

            if '=' in v:
                raise ParsingError(
                    line_nb,
                    f"Invalid metadata entry: '{pair}'"
                    )
            metadata[k] = v

        if not set(metadata.keys()).issubset(md_keys):
            raise ParsingError(
                    line_nb,
                    "Metadata block contains invalid key-value pairs\n" +
                    f"Valid keys: {md_keys}"
                    )

        return metadata

    def get_map_bounds(self) -> tuple[int, int, int, int]:
        if not self.zones:
            raise ValueError("No zones defined")

        xs = [zone.x for zone in self.zones.values()]
        ys = [zone.y for zone in self.zones.values()]

        return (
            min(xs), max(xs),
            min(ys), max(ys),
            )
