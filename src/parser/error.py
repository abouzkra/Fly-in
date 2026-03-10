class ParsingError(Exception):
    def __init__(self, line_nb: int, msg: str) -> None:
        super().__init__(f"Parsing error on line {line_nb}: {msg}")
        self.line_nb: int = line_nb
        self.msg: str = msg
