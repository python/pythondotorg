import os
import subprocess

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

PIPELINE_COMPILERS = (
  'pipeline.compilers.sass.SASSCompiler',
)
PIPELINE_SASS_BINARY = 'cd %s && exec /usr/bin/env sass'  % os.path.join(BASE, 'static')
PIPELINE_SASS_ARGUMENTS = '--quiet --compass --scss -I $(dirname $(dirname $(gem which susy)))/sass'

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'

# Homebrew installs yuicompressor as "yuicompressor", but Apt installs it as
# "yui-compressor". FLAIL.
for yuicompressor in ['yuicompressor', 'yui-compressor']:
    if subprocess.call(['which', yuicompressor], stdout=subprocess.PIPE) == 0:
        PIPELINE_YUI_BINARY = yuicompressor
        break
else:
    import warnings
    warnings.warn("No yuicompressor found; this means collectstatic won't work.")
