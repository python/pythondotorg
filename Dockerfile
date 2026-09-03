FROM ghcr.io/astral-sh/uv:0.12.9@sha256:8b940d3a9d65bed080436972241af2e21c84b5e8c9193f7014ed71479ee795ff AS uv

FROM python:3.14.7-bookworm
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# By default, Docker has special steps to avoid keeping APT caches in the layers, which
# is good, but in our case, we're going to mount a special cache volume (kept between
# builds), so we WANT the cache to persist.
RUN set -eux; \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache;

# Install System level build requirements, this is done before
# everything else because these are rarely ever going to change.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -x \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-fonts-recommended \
        texlive-plain-generic \
        lmodern

RUN case $(uname -m) in \
         "x86_64")  ARCH=amd64 ;; \
         "aarch64")  ARCH=arm64 ;; \
    esac \
    && wget --quiet https://github.com/jgm/pandoc/releases/download/2.17.1.1/pandoc-2.17.1.1-1-${ARCH}.deb \
    && dpkg -i pandoc-2.17.1.1-1-${ARCH}.deb

RUN mkdir /code
WORKDIR /code

COPY --from=uv /uv /uvx /usr/local/bin/

COPY pyproject.toml uv.lock /code/

RUN --mount=type=cache,target=/root/.cache \
    set -x \
    && uv sync \
         --frozen \
         --no-editable \
         --no-install-project

COPY . /code/

RUN uv sync \
      --frozen \
      --no-editable
