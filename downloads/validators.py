"""Model validators for the Downloads app."""

from django.core.exceptions import ValidationError
from django.core import validators

is_valid_python_release = validators.RegexValidator(
    regex=r'^Python\s[\d.]+$',
    message="Release name must be in the format 'Python X.Y.Z' (e.g., 'Python 3.14.0')"
)
