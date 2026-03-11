class ParsingError(Exception):
    """Exception raised when a parsing error occurs.

    Attributes:
        line_nb (int): The line number where the error occurred.
        msg (str): The error message describing the parsing error.
    """
    def __init__(self, line_nb: int, msg: str) -> None:
        """Initialize the ParsingError with the line number and error message.

        Args:
            line_nb (int): The line number where the error occurred.
            msg (str): The error message describing the parsing error.
        """
        super().__init__(f"Parsing error on line {line_nb}: {msg}")
        self.line_nb: int = line_nb
        self.msg: str = msg
