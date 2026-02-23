import sys
from models import Map, ParsingError
# from visualizer import launch_visualizer


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)

    file = sys.argv[1]

    m = None
    try:
        m = Map()
        
        m.parse_file(file)

    except ParsingError as e:
        print(e)
        sys.exit(1)

    # try:
    #     launch_visualizer(m)
    # except Exception as e:
    #     print(f"Visualiser Error: {e}")
    #     sys.exit(1)


if __name__ == "__main__":
    main()
