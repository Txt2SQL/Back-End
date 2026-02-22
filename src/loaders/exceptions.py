class LoaderError(Exception):
    """Base loader exception."""


class EnvFileNotFoundError(LoaderError):
    pass


class MissingVariableError(LoaderError):
    pass


class UninitializedVariableError(LoaderError):
    pass


class InvalidTypeError(LoaderError):
    pass


class ConnectionTestError(LoaderError):
    pass