from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


def get_static_image_file_as_upload(filename, upload_filename):
    static_images_dir = Path(settings.STATICFILES_DIRS[0]) / "img"
    img = static_images_dir / filename
    assert img.exists(), f"File {img} does not exist"
    with img.open("rb") as fd:
        return SimpleUploadedFile(upload_filename, fd.read())


def assertMessage(msg, expected_content, expected_level):
    assert msg.level == expected_level, f"Message {msg} level is not {expected_level}"
    assert (
        str(msg) == expected_content
    ), f"Message {msg} content is not {expected_content}"
