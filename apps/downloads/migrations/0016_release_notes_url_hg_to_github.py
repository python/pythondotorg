"""Rewrite dead hg.python.org release notes URLs to their GitHub equivalents."""

import re

from django.db import migrations

HG_URL_RE = re.compile(r"^https?://hg\.python\.org/cpython/(?:raw-)?file/(?P<ref>[^/]+)/(?P<path>.+)$")
GITHUB_BLOB_URL = "https://github.com/python/cpython/blob/{ref}/{path}"

# Mercurial changesets do not exist in git; map the ones stored in production
# to the git ref for the same release.
HG_CHANGESET_TO_GIT_REF = {
    "15fc83c505e3": "b34ba3f174ced8b6534888179b2f22e0f006c26e",  # 2.3 (no v2.3 tag in git)
    "e32e3a9f3902": "v2.7.7rc1",
    "80ccce248ba2": "v2.7.10rc1",
    "15c95b7d81dc": "v2.7.10",
    "82dd9545bd93": "v2.7.11rc1",
    "53d30ab403f1": "v2.7.11",
}


def github_url_for(hg_url):
    match = HG_URL_RE.match(hg_url)
    if match is None:
        return None
    ref = match["ref"]
    if not ref.startswith("v"):
        ref = HG_CHANGESET_TO_GIT_REF.get(ref)
        if ref is None:
            return None
    return GITHUB_BLOB_URL.format(ref=ref, path=match["path"])


def rewrite_hg_release_notes_urls(apps, schema_editor):
    Release = apps.get_model("downloads", "Release")
    db_alias = schema_editor.connection.alias
    releases = Release.objects.using(db_alias).filter(release_notes_url__contains="hg.python.org")
    for release in releases:
        url = github_url_for(release.release_notes_url)
        if url is not None:
            Release.objects.using(db_alias).filter(pk=release.pk).update(release_notes_url=url)


class Migration(migrations.Migration):
    dependencies = [
        ("downloads", "0015_releasefile_python_dot_org_urls"),
    ]

    operations = [
        migrations.RunPython(rewrite_hg_release_notes_urls, migrations.RunPython.noop),
    ]
