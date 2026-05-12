from typing import Any
from webcolors import name_to_rgb
from random import randint
from error import ParsingError
from zone import Zone, ZoneType, Neighbor


class Map:
    """Parser for the map definition file, which contains the zones and
    connection definitions. The expected format of the file is as follows:
        nb_drones: <positive_integer>
        start_hub: <name> <x> <y>
        end_hub: <name> <x> <y>
        hub: <name> <x> <y>
        connection: <zone1> <zone2>

    Attributes:
        nb_drones: The number of drones in the simulation
        start_zone: The name of the starting zone
        end_zone: The name of the ending zone
        zones: A dictionary mapping zone names to Zone objects
        connections: A list of tuples representing the connections between
            zones
    """
    def __init__(self) -> None:
        """Initializes the Map object with default values."""
        self.nb_drones: int = 0
        self.start_zone: str = ""
        self.end_zone: str = ""
        self.zones: dict[str, Zone] = {}
        self.connections: list[tuple[str, str]] = list()

    def parse_file(self, input_file: str) -> None:
        """Parses the input file and populates the Map object with the defined
        zones and connections.

        Args:
            input_file: The path to the input file containing the map
                definition

        Raises:
            ParsingError: If the input file contains invalid syntax or if there
                are issues with the defined zones or connections
                (e.g., duplicate zone names, undefined zones in connections,
                etc.)
        """
        with open(input_file, 'r') as file:
            for line_nb, line in enumerate(file, start=1):
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if self.nb_drones == 0:
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

            if not self.start_zone:
                raise ParsingError(-1, "Missing start_hub definition")
            if not self.end_zone:
                raise ParsingError(-1, "Missing end_hub definition")

    def _parse_nb_drones(self, line: str, line_nb: int) -> None:
        """Parses the number of drones from the input line.

        Args:
            line: The input line containing the number of drones definition
            line_nb: The line number in the input file

        Raises:
            ParsingError: If the line does not start with "nb_drones:"
                or if the value is not a positive integer
        """
        if line.startswith('nb_drones:'):
            try:
                self.nb_drones = int(line.split(':', 1)[1].strip())
            except ValueError as e:
                raise ParsingError(line_nb, str(e))
        else:
            raise ParsingError(
                line_nb,
                "Input file must start with: " +
                "\"nb_drones: <positive_integer>\""
                )

        if self.nb_drones <= 0:
            raise ParsingError(
                line_nb,
                "nb_drones must be a positive integer"
                )

    def _parse_zone(self, line: str, line_nb: int, zone_kind: str) -> None:
        """Parses a zone definition from the input line and adds it to the Map
        object.

        Args:
            line: The input line containing the zone definition
            line_nb: The line number in the input file
            zone_kind: The type of the zone being parsed (e.g., "start",
                "end", "hub")

        Raises:
            ParsingError: If the line does not follow the expected format for
                zone definitions, if there are duplicate zone names, if the
                zone type is invalid, if the color name is invalid, or if
                there are zones with duplicate coordinates.
        """
        metadata_str = ""

        if "[" in line:
            line, metadata_str = line.split('[', 1)
            metadata_str = "[" + metadata_str

        tokens = line.split()
        if len(tokens) != 4:
            raise ParsingError(
                line_nb,
                "Invalid zone definition format, syntax:\n" +
                "\t\"<zone_kind>: <name> <x> <y> [metadata]\""
                )

        _, name, x, y = tokens

        metadata = self._parse_metadata(
                metadata_str, line_nb,
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
            color_name = metadata['color']
            if color_name == 'rainbow':
                color = -1
            else:
                rgb = name_to_rgb(color_name)
                color = (
                    (rgb.red << 24) | (rgb.green << 16) | (rgb.blue << 8) | 255
                    )
        except (ValueError, KeyError):
            r = randint(0, 255)
            g = randint(0, 255)
            b = randint(0, 255)
            color = (r << 24) | (g << 16) | (b << 8) | 255

        try:
            zone = Zone(
                    name=name,
                    x=int(x), y=int(y),
                    zone_type=zone_type,
                    max_drones=metadata.get('max_drones', 1),
                    color=color
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
            zone.zone_type = ZoneType.NORMAL
            zone.max_drones = self.nb_drones
            self.start_zone = name

        if zone_kind == 'end':
            if self.end_zone:
                raise ParsingError(
                    line_nb,
                    "Found multiple end_hub definitions"
                    )
            zone.zone_type = ZoneType.NORMAL
            zone.max_drones = self.nb_drones
            self.end_zone = name

        self.zones[name] = zone

    def _parse_connection(self, line: str, line_nb: int) -> None:
        """Parses a connection definition from the input line and adds it to
        the Map object.

        Args:
            line: The input line containing the connection definition
            line_nb: The line number in the input file

        Raises:
            ParsingError: If the line does not follow the expected format for
                connection definitions, if there are duplicate connections, if
                the connection references undefined zones, or if the
                max_link_capacity value is invalid.
        """
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

        edge = (zone1, zone2)

        if sorted(edge) in [sorted(e) for e in self.connections]:
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
        """Parses a metadata string from the input line and returns a
        dictionary of key-value pairs.

        Args:
            raw_md: The raw metadata string (including brackets) to be parsed
            line_nb: The line number in the input file
            md_keys: A set of expected metadata keys that can be used in the
                metadata
        """
        raw_md = raw_md.strip()[1: -1]

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

            if '=' in v or not v:
                raise ParsingError(
                    line_nb,
                    f"Invalid metadata entry: '{pair}'"
                    )
            if k in metadata:
                raise ParsingError(
                    line_nb,
                    f"Duplicate metadata key: '{k}'"
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
        """Returns the minimum and maximum x and y coordinates of the zones
        defined in the Map object.

        Returns:
            A tuple containing the minimum x, maximum x, minimum y, and maximum
            y coordinates of the zones

        Raises:
            ValueError: If there are no zones defined in the Map object
        """
        if not self.zones:
            raise ValueError("No zones defined")

        xs = [zone.x for zone in self.zones.values()]
        ys = [zone.y for zone in self.zones.values()]

        return (
            min(xs), max(xs),
            min(ys), max(ys),
            )
