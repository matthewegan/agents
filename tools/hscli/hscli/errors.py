"""Exit codes and exception types.

Stable exit codes let calling agents distinguish failure modes without parsing
error text. Keep these values stable across versions.

Exit code 2 is reserved for Click/Typer UsageError (bad CLI arguments).
"""

EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_NOT_FOUND = 3
EXIT_VALIDATION = 4
EXIT_CONFIG = 5
EXIT_AUTH = 10


class HSError(Exception):
    exit_code = EXIT_GENERAL


class ConfigError(HSError):
    exit_code = EXIT_CONFIG


class AuthError(HSError):
    exit_code = EXIT_AUTH


class NotFoundError(HSError):
    exit_code = EXIT_NOT_FOUND


class ValidationError(HSError):
    exit_code = EXIT_VALIDATION
