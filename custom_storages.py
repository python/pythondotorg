from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin, StaticFilesStorage

from pipeline.storage import PipelineMixin
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = settings.MEDIAFILES_LOCATION


class PipelineManifestStorage(PipelineMixin, ManifestFilesMixin, StaticFilesStorage):
    """
    Override the replacement patterns to match URL-encoded quotations.
    """
    patterns = (
        ("*.css", (
            r"""(url\((?:['"]|%22|%27){0,1}\s*(.*?)(?:['"]|%22|%27){0,1}\))""",
            (r"""(@import\s*["']\s*(.*?)["'])""", """@import url("%s")"""),
        )),
    )
