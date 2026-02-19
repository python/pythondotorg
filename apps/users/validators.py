"""Custom username validators for allauth registration."""

from django.contrib.auth.validators import ASCIIUsernameValidator

username_validators = [ASCIIUsernameValidator()]
