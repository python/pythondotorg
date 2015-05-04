# Require any additional compass plugins here.
require "compass/import-once/activate"


# Set this to the root of your project when deployed:
http_path = "../"
sass_dir = "sass"
images_dir = "img"
javascripts_dir = "js"
fonts_dir = "fonts"
css_dir = "stylesheets"
sourcemap = true


add_import_path "sass/framework"
add_import_path "sass/libraries"
add_import_path "sass/project"
add_import_path "sass/templates"
add_import_path "sass/variables"


# You can select your preferred output style here (can be overridden via the command line):
# Compass needs to RESTART before a new style will take effect
# output_style = :expanded or :nested or :compact or :compressed
# expanded = kept as written, all comments intact
# nested = kept as written, comments intact, indents added to show nesting
# compact = all one line, retains comments
# compressed = all comments and spacing removed
output_style = :compressed

# To enable relative paths to assets via compass helper functions. Uncomment:
# relative_assets = true

# To disable debugging comments that display the original location of your selectors. Uncomment:
# line_comments = false


# If you prefer the indented syntax, you might want to regenerate this
# project again passing --syntax sass, or you can uncomment this:
# preferred_syntax = :sass
# and then run:
# sass-convert -R --from scss --to sass sass scss && rm -rf sass && mv scss sass

# Expect UTF-8 encoded scss stylesheets by default.
Encoding.default_external = "UTF-8"
