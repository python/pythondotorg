import datetime as dt
import json
import os
import re
from collections import defaultdict

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic.base import RedirectView, TemplateView

from codesamples.models import CodeSample
from downloads.models import Release


def health(request):
    return HttpResponse("OK")


def serve_funding_json(request):
    """Serve the funding.json file from the static directory."""
    funding_json_path = os.path.join(settings.BASE, "static", "funding.json")
    try:
        with open(funding_json_path) as f:
            data = json.load(f)
        return JsonResponse(data)
    except FileNotFoundError:
        return JsonResponse({"error": "funding.json not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in funding.json"}, status=500)


class IndexView(TemplateView):
    template_name = "python/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "code_samples": CodeSample.objects.published()[:5],
            }
        )
        return context


class AuthenticatedView(TemplateView):
    template_name = "includes/authenticated.html"


class DocumentationIndexView(TemplateView):
    template_name = "python/documentation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "latest_python2": Release.objects.latest_python2(),
                "latest_python3": Release.objects.latest_python3(),
            }
        )
        return context


class MediaMigrationView(RedirectView):
    prefix = None
    permanent = True
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        image_path = kwargs["url"]
        if self.prefix:
            image_path = "/".join([self.prefix, image_path])
        return "/".join(
            [
                settings.AWS_S3_ENDPOINT_URL,
                settings.AWS_STORAGE_BUCKET_NAME,
                image_path,
            ]
        )


class DocsByVersionView(TemplateView):
    template_name = "python/versions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        releases = Release.objects.filter(
            is_published=True,
            pre_release=False,
        ).order_by("-release_date")

        # Some releases have no documentation
        no_docs = {"2.3.6", "2.3.7", "2.4.5", "2.4.6", "2.5.5", "2.5.6"}

        # We'll group releases by major.minor version
        version_groups = defaultdict(list)

        for release in releases:
            # Extract version number from name ("Python 3.14.0" -> "3.14.0")
            version_match = re.match(r"Python ([\d.]+)", release.name)
            if version_match:
                full_version = version_match.group(1)

                if full_version in no_docs:
                    continue

                # Get major.minor version ("3.14.0" -> "3.14")
                version_parts = full_version.split(".")
                major_minor = f"{version_parts[0]}.{version_parts[1]}"

                # For 3.2.0 and earlier, use X.Y instead of X.Y.0
                if len(version_parts) == 3:
                    major, minor, patch = map(int, version_parts)
                    # For versions <= 3.2.0 where patch is 0
                    if (major, minor, patch) <= (3, 2, 0) and patch == 0:
                        full_version = major_minor

                release_data = {
                    "stage": full_version,
                    "date": release.release_date.replace(tzinfo=None),
                }
                version_groups[major_minor].append(release_data)

        # Add legacy releases not in the database
        legacy_releases_data = {
            "2.2": [
                {"stage": "2.2p1", "date": dt.datetime(2002, 3, 29)},
            ],
            "2.1": [
                {"stage": "2.1.2", "date": dt.datetime(2002, 1, 16)},
                {"stage": "2.1.1", "date": dt.datetime(2001, 7, 20)},
                {"stage": "2.1", "date": dt.datetime(2001, 4, 15)},
            ],
            "2.0": [
                {"stage": "2.0", "date": dt.datetime(2000, 10, 16)},
            ],
            "1.6": [
                {"stage": "1.6", "date": dt.datetime(2000, 9, 5)},
            ],
            "1.5": [
                {"stage": "1.5.2p2", "date": dt.datetime(2000, 3, 22)},
                {"stage": "1.5.2p1", "date": dt.datetime(1999, 7, 6)},
                {"stage": "1.5.2", "date": dt.datetime(1999, 4, 30)},
                {"stage": "1.5.1p1", "date": dt.datetime(1998, 8, 6)},
                {"stage": "1.5.1", "date": dt.datetime(1998, 4, 14)},
                {"stage": "1.5", "date": dt.datetime(1998, 2, 17)},
            ],
            "1.4": [
                {"stage": "1.4", "date": dt.datetime(1996, 10, 25)},
            ],
        }

        # Merge legacy releases in
        for version, items in legacy_releases_data.items():
            version_groups[version].extend(items)

        # Convert to list for template and sort releases within each version
        version_list = []
        for version, releases in version_groups.items():
            # Sort x.y.z newest first
            releases = sorted(
                releases,
                key=lambda x: x.get("date", dt.datetime.min),
                reverse=True,
            )
            for release in releases:
                release["date"] = release["date"].strftime("%-d %B %Y")

            version_list.append(
                {
                    "version": version,
                    "releases": releases,
                }
            )

        # Sort x.y versions (newest first)
        version_list.sort(
            key=lambda x: [int(n) if n.isdigit() else n for n in x["version"].split(".")],
            reverse=True,
        )

        context.update(
            {
                "version_list": version_list,
            }
        )

        return context
