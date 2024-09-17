from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag
def render_template_for(obj, template=None, template_directory=None):
    """
    Renders a template based on the `media_type` of the given object in the
    given template directory, falling back to default.html.

    If no `template_directory` is specified the default path is `community/types`
    with a fall-back of `community/types/default.html`.

    The object passed to the tag will be available as `object`.

    Syntax::

        {% render_template_for object [template=template_name] [template_directory=None] as html %}

    Example::

        {% render_template_for object template='allthings.html' as html %}

        {% render_template_for object template_directory='includes/types' as html %}

    """
    context = {
        'object': obj,
    }

    template_list = []
    if template:
        template_list.append(template)

    template_dirs = []
    if template_directory:
        template_dirs.append(template_directory)

    template_dirs.append('community/types')

    for directory in template_dirs:
        template_list.append(f'{directory}/{obj.get_media_type_display()}.html')
        template_list.append(f'{directory}/default.html')

    output = render_to_string(template_list, context)
    return output
