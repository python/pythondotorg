.. _downloads_api:

Downloads API
=============

The python.org Downloads API provides programmatic, machine-readable access
to Python operating systems, releases, and downloadable release files (such as
installers, source tarballs, checksums, GPG signatures, Sigstore attestations,
and SPDX-2 Software Bill of Materials [SBOM]).

The API is available under two versions:

- **v1 API (Tastypie)**: Base path ``/api/v1/downloads/``
- **v2 API (Django REST Framework)**: Base path ``/api/v2/downloads/``

Both APIs support JSON responses and provide read-only public access to published
releases. Staff credentials are required for creating, modifying, or deleting
records, or for viewing unpublished drafts.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview and Authentication
---------------------------

Public Read Access
~~~~~~~~~~~~~~~~~~

Anyone can query published operating systems, releases, and release files without
authentication using HTTP ``GET`` requests.

- For unauthenticated users, the API automatically filters out unpublished drafts
  (``is_published=False``).
- Responses are returned with ``Content-Type: application/json``.

Staff Write Access
~~~~~~~~~~~~~~~~~~

Creating, modifying, or deleting resources, as well as viewing unpublished draft
releases, requires an authenticated staff user:

- **v1 (Tastypie)**: Supply an API key in the ``Authorization`` header:

  .. code-block:: text

     Authorization: ApiKey <username>:<api_key>

- **v2 (Django REST Framework)**: Supply a token in the ``Authorization`` header:

  .. code-block:: text

     Authorization: Token <token_key>

Write operations without staff privileges return ``401 Unauthorized`` or ``403 Forbidden``.

Rate Limiting
~~~~~~~~~~~~~

The v1 API applies a cache-based rate throttle of 600 requests per hour for guest
users. The v2 API uses standard Django and Fastly caching infrastructure.

----

Endpoints (v2 - Django REST Framework)
--------------------------------------

The v2 API is built with Django REST Framework and is available under ``/api/v2/downloads/``.

Operating Systems: ``/api/v2/downloads/os/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lists or retrieves supported operating systems (such as Windows, macOS, Linux/Source).

- **List endpoint**: ``GET /api/v2/downloads/os/``
- **Detail endpoint**: ``GET /api/v2/downloads/os/<id>/``
- **Allowed methods**: ``GET`` (all users), ``POST``, ``PUT``, ``PATCH``, ``DELETE`` (staff only)

Query Parameters:
  :``name``: Filter by exact operating system name (e.g., ``?name=Windows``).
  :``slug``: Filter by exact operating system slug (e.g., ``?slug=windows``).

Sample Response (``GET /api/v2/downloads/os/``):

.. code-block:: json

   [
     {
       "name": "Windows",
       "slug": "windows",
       "resource_uri": "https://www.python.org/api/v2/downloads/os/1/"
     },
     {
       "name": "macOS",
       "slug": "macos",
       "resource_uri": "https://www.python.org/api/v2/downloads/os/2/"
     },
     {
       "name": "Source",
       "slug": "source",
       "resource_uri": "https://www.python.org/api/v2/downloads/os/3/"
     }
   ]

Releases: ``/api/v2/downloads/release/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lists or retrieves Python releases.

- **List endpoint**: ``GET /api/v2/downloads/release/``
- **Detail endpoint**: ``GET /api/v2/downloads/release/<id>/``
- **Allowed methods**: ``GET`` (all users), ``POST``, ``PUT``, ``PATCH``, ``DELETE`` (staff only)

Query Parameters:
  :``name``: Filter by exact release name (e.g., ``?name=Python%203.13.0``).
  :``slug``: Filter by release slug (e.g., ``?slug=python-3130``).
  :``version``: Filter by major version family:
    - ``1``: Python 1.x.x
    - ``2``: Python 2.x.x
    - ``3``: Python 3.x.x
    - ``100``: Python install manager
  :``pre_release``: Boolean filter for pre-releases (``?pre_release=true`` or ``?pre_release=false``).
  :``is_published``: Boolean filter (non-staff users can only query ``true``).
  :``release_date``: Filter by exact ISO 8601 release timestamp.

Sample Response (``GET /api/v2/downloads/release/``):

.. code-block:: json

   [
     {
       "name": "Python 3.13.0",
       "slug": "python-3130",
       "version": 3,
       "is_published": true,
       "is_latest": true,
       "release_date": "2024-10-07T00:00:00Z",
       "pre_release": false,
       "release_page": "https://www.python.org/doc/versions/",
       "release_notes_url": "https://docs.python.org/release/3.13.0/whatsnew/changelog.html",
       "show_on_download_page": true,
       "resource_uri": "https://www.python.org/api/v2/downloads/release/1/"
     }
   ]

Release Files: ``/api/v2/downloads/release_file/``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lists or retrieves downloadable files, installers, source tarballs, signatures, and SBOM metadata associated with Python releases.

- **List endpoint**: ``GET /api/v2/downloads/release_file/``
- **Detail endpoint**: ``GET /api/v2/downloads/release_file/<id>/``
- **Allowed methods**: ``GET`` (all users), ``POST``, ``PUT``, ``PATCH``, ``DELETE`` (staff only)

Query Parameters:
  :``name``: Filter by exact file name.
  :``slug``: Filter by file slug.
  :``description``: Filter by substring contained in description (``?description__contains=installer``).
  :``os``: Filter by operating system database ID (e.g., ``?os=1``).
  :``release``: Filter by release database ID (e.g., ``?release=1``).

Batch Deletion by Release:
  Staff users can delete all files associated with a single release:

  .. code-block:: text

     DELETE /api/v2/downloads/release_file/delete_by_release/?release=<release_id>

Sample Response (``GET /api/v2/downloads/release_file/?release=1``):

.. code-block:: json

   [
     {
       "name": "Windows installer (64-bit)",
       "slug": "windows-installer-64-bit",
       "os": "https://www.python.org/api/v2/downloads/os/1/",
       "release": "https://www.python.org/api/v2/downloads/release/1/",
       "description": "Recommended for most 64-bit Windows installations",
       "is_source": false,
       "url": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe",
       "gpg_signature_file": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe.asc",
       "sigstore_signature_file": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe.sig",
       "sigstore_cert_file": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe.crt",
       "sigstore_bundle_file": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe.sigstore",
       "sbom_spdx2_file": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe.spdx.json",
       "md5_sum": "0123456789abcdef0123456789abcdef",
       "sha256_sum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
       "filesize": 25680128,
       "download_button": true,
       "resource_uri": "https://www.python.org/api/v2/downloads/release_file/10/"
     }
   ]

----

Endpoints (v1 - Tastypie)
-------------------------

The v1 API is powered by Tastypie and available under ``/api/v1/downloads/``.

Resources:
  :``/api/v1/downloads/os/``: Operating systems resource.
  :``/api/v1/downloads/release/``: Python releases resource.
  :``/api/v1/downloads/release_file/``: Release files resource.

Envelope and Pagination
~~~~~~~~~~~~~~~~~~~~~~~

Tastypie wraps list responses in a top-level dictionary containing ``meta`` and ``objects``:

.. code-block:: json

   {
     "meta": {
       "limit": 20,
       "next": null,
       "offset": 0,
       "previous": null,
       "total_count": 3
     },
     "objects": [
       {
         "name": "Windows",
         "slug": "windows",
         "resource_uri": "/api/v1/downloads/os/1/"
       }
     ]
   }

Pagination Parameters:
  :``limit``: Number of items per page (default: 20).
  :``offset``: Zero-based starting position in the result set.

Release Filtering in v1:
  :``version``: Exact version family match (``?version=3``).
  :``version__startswith``: Starts-with match on version integer.
  :``pre_release``: Boolean match (``?pre_release=false``).
  :``release_date``: Date filtering with standard Tastypie operators (``__exact``, ``__gte``, ``__lte``).

Release File Deletion in v1:
  Staff users can bulk-delete files scoped to a single release:

  .. code-block:: text

     DELETE /api/v1/downloads/release_file/?release=<release_id>

  The request must include exactly one ``release`` query parameter.

----

URL Validation Rules for Release Files
--------------------------------------

To protect users against supply chain tampering and unauthorized mirrors, the
application enforces strict security validation on release file writes:

1. **Python.org Prefix**: All artifact and sidecar URLs must begin with
   ``https://www.python.org/`` (legacy HTTP entries are read-only).
2. **Sidecar Suffix Constraints**: Sidecar URLs must match the primary artifact
   URL with their respective standard extension:
   - GPG Signature: ``<artifact_url>.asc``
   - Sigstore Signature: ``<artifact_url>.sig``
   - Sigstore Certificate: ``<artifact_url>.crt``
   - Sigstore Bundle: ``<artifact_url>.sigstore``
   - SPDX-2 SBOM: ``<artifact_url>.spdx.json``
3. **Supernav Button Constraint**: At most one release file per operating system
   and release may have ``download_button=True``.
