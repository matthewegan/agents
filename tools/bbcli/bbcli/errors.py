"""Exit codes and exception types.

Stable exit codes let calling agents distinguish failure modes without parsing
error text. Keep these values stable across versions.
"""

EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_AUTH = 2
EXIT_NOT_FOUND = 3
EXIT_VALIDATION = 4
EXIT_CONFIG = 5


class BBError(Exception):
    exit_code = EXIT_GENERAL


class ConfigError(BBError):
    exit_code = EXIT_CONFIG


class AuthError(BBError):
    exit_code = EXIT_AUTH


class NotFoundError(BBError):
    exit_code = EXIT_NOT_FOUND


class ValidationError(BBError):
    exit_code = EXIT_VALIDATION
