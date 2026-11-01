"""Utility functions for the sponsors app."""

from pathlib import Path


def file_from_storage(filename, mode, storage):
    """Open a file in the explicit backend, creating its local parent if needed."""
    try:
        # if using S3 Storage the file will always exist
        file = storage.open(filename, mode)
    except FileNotFoundError as e:
        # local env, not using S3
        path = Path(e.filename).parent
        if not path.exists():
            path.mkdir(parents=True)
        Path(e.filename).touch()
        file = storage.open(filename, mode)

    return file


def with_article(word):
    """Prefix ``word`` with the indefinite article that reads correctly ("an Approved", "a Draft")."""
    article = "an" if word and word[0].lower() in "aeiou" else "a"
    return f"{article} {word}"
