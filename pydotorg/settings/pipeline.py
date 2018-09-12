import os

from .base import BASE

PIPELINE_CSS = {
    'style': {
        'source_filenames': (
            'sass/style.css',
        ),
        'output_filename': 'stylesheets/style.css',
        'extra_context': {
            'title': 'default',
            'media': '',
        },
    },
    'mq': {
        'source_filenames': (
            'sass/mq.css',
        ),
        'output_filename': 'stylesheets/mq.css',
        'extra_context': {
            'media': 'not print, braille, embossed, speech, tty',
        },
    },
    'no-mq': {
        'source_filenames': (
            'sass/no-mq.css',
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
    # TODO: ruby-sass is not installed on the server since
    # https://github.com/python/psf-salt/commit/044c38773ced4b8bbe8df2c4266ef3a295102785
    # and we pre-compile SASS files and commit them into codebase so we
    # don't really need this. See issue #832.
    # 'COMPILERS': (
    #     'pipeline.compilers.sass.SASSCompiler',
    # ),
    'CSS_COMPRESSOR': 'pipeline.compressors.yui.YUICompressor',
    'JS_COMPRESSOR': 'pipeline.compressors.yui.YUICompressor',
    # It's yui-compressor no yuicompressor on some systems.
    'YUI_BINARY': '/usr/bin/env yui-compressor',
    # 'SASS_BINARY': 'cd %s && exec /usr/bin/env sass'  % os.path.join(BASE, 'static'),
    # 'SASS_ARGUMENTS': '--quiet --compass --scss -I $(dirname $(dirname $(gem which susy)))/sass'
}
