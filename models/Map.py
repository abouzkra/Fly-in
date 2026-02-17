from typing import Any
from .Error import ParsingError
from .Zone import Zone, ZoneType


class Map:
    def __init__(self):
        self.nb_drones: int = 0
        self.start_zone: str | None = None
        self.end_zone: str | None = None
        self.zones: dict[str, Zone] = {}
        self.connections: set[tuple[str, str]] = set()

    def parse_file(self, input_file: str) -> None:
        with open(input_file, 'r') as file:
            for line_nb, line in enumerate(file, start=1):
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if not self.nb_drones:
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

            print(self.nb_drones)
            print(self.start_zone)
            print(self.end_zone)
            print(self.zones)
            print(self.connections)

    def _parse_nb_drones(self, line: str, line_nb: int) -> None:
        if line.startswith('nb_drones:'):
            try:
                self.nb_drones = int(line.split(':')[1].strip())
            except Exception as e:
                raise ParsingError(line_nb, str(e))
        else:
            raise ParsingError(
                line_nb,
                "Input file must start with: \"nb_drones': <positive_integer>\""
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

        metadata = self._parse_metadata(metadata, line_nb, 'zone')

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

        self.zones[name] = zone

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

    def _parse_connection(self, line: str, line_nb: int):
        pass

    def _parse_metadata(
            self,
            raw_md: str,
            line_nb: int,
            md_type: str
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
            k, v = pair.split('=', 1)

            if '=' not in pair or not v:
                raise ParsingError(
                    line_nb,
                    f"Invalid metadata entry: '{pair}'"
                    )

            metadata[k] = v

        if(
            md_type == 'zone'
            and not set(metadata.keys()).issubset(
                {'zone', 'color', 'max_drones'}
                )
            ):
            raise ParsingError(
                    line_nb,
                    "Metadata block contains invalid key-value pairs"
                    )

        if(
            md_type == 'conn'
            and not set(metadata.keys()).issubset({'max_link_capacity'})
            ):
            raise ParsingError(
                    line_nb,
                    "Metadata block contains invalid key-value pairs"
                    )
        
        return metadata


if __name__ == "__main__":
    m = Map()

    m.parse_file("maps/easy/01_linear_path.txt")
