import os

from .base import BASE

PIPELINE_CSS = {
    'style': {
        'source_filenames': (
            'sass/style.scss',
        ),
        'output_filename': 'stylesheets/style.css',
        'extra_context': {
            'title': 'default',
            'media': '',
        },
    },
    'mq': {
        'source_filenames': (
            'sass/mq.scss',
        ),
        'output_filename': 'stylesheets/mq.css',
        'extra_context': {
            'media': 'not print, braille, embossed, speech, tty',
        },
    },
    'no-mq': {
        'source_filenames': (
            'sass/no-mq.scss',
        ),
        'output_filename': 'stylesheets/no-mq.css',
        'extra_context': {
            'media': 'screen',
        },
    },
}

PIPELINE_JS = {
    'main': {
        'source_filenames': (
            'js/plugins.js',
            'js/script.js',
        ),
        'output_filename': 'js/main-min.js',
    },
    'IE8': {
        'source_filenames': (
            'js/plugins/IE8.js',
        ),
        'output_filename': 'js/plugins/IE8-min.js',
    },
    'getComputedStyle': {
        'source_filenames': (
            'js/plugins/getComputedStyle-min.js',
        ),
        'output_filename': 'js/plugins/getComputedStyle-min.js',
    },
}

PIPELINE = {
    'STYLESHEETS': PIPELINE_CSS,
    'JAVASCRIPT': PIPELINE_JS,
    'COMPILERS': (
        'pipeline.compilers.sass.SASSCompiler',
    ),
    'CSS_COMPRESSOR': 'pipeline.compressors.yui.YUICompressor',
    'JS_COMPRESSOR': 'pipeline.compressors.yui.YUICompressor',
    'SASS_BINARY': 'cd %s && exec /usr/bin/env sass'  % os.path.join(BASE, 'static'),
    'SASS_ARGUMENTS': '--quiet --compass --scss -I $(dirname $(dirname $(gem which susy)))/sass'
}
