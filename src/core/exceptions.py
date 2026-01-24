"""Custom exceptions for the converter."""


class ConversionError(Exception):
    """Base exception for conversion errors."""
    pass


class ConversionCancelled(ConversionError):
    """Raised when the user cancels the conversion."""
    pass


class FileAccessError(ConversionError):
    """Raised when a file cannot be read or written."""
    pass
