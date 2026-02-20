import sys
from models import Map, ParsingError


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    file = sys.argv[1]

    try:
        m = Map()
        
        m.parse_file(file)

        print("Map parsed successfully!")
    except ParsingError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
