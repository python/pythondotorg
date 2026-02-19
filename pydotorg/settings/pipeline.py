"""Django Pipeline configuration for CSS and JavaScript asset compilation."""

PIPELINE_CSS = {
    "style": {
        "source_filenames": ("css/style.css",),
        "output_filename": "stylesheets/style.css",
        "extra_context": {
            "title": "default",
            "media": "",
        },
    },
    "mq": {
        "source_filenames": ("css/mq.css",),
        "output_filename": "stylesheets/mq.css",
        "extra_context": {
            "media": "not print, braille, embossed, speech, tty",
        },
    },
    "font-awesome": {
        "source_filenames": ("stylesheets/font-awesome.min.css",),
        "output_filename": "stylesheets/font-awesome.css",
        "extra_context": {
            "media": "screen",
        },
    },
}

PIPELINE_JS = {
    "main": {
        "source_filenames": (
            "js/plugins.js",
            "js/script.js",
        ),
        "output_filename": "js/main-min.js",
    },
    "sponsors": {
        "source_filenames": ("js/sponsors/applicationForm.js",),
        "output_filename": "js/sponsors-min.js",
    },
}

PIPELINE = {
    "STYLESHEETS": PIPELINE_CSS,
    "JAVASCRIPT": PIPELINE_JS,
    "DISABLE_WRAPPER": True,
    "CSS_COMPRESSOR": "pipeline.compressors.NoopCompressor",
    "JS_COMPRESSOR": "pipeline.compressors.NoopCompressor",
}
