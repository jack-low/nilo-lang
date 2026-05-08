class NiloError(Exception):
    """Base error for user-facing Nilo failures."""


class LexError(NiloError):
    pass


class ParseError(NiloError):
    pass


class RuntimeError(NiloError):
    pass
