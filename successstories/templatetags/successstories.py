from django import template

from ..models import Story, StoryCategory


register = template.Library()


@register.assignment_tag
def get_story_categories():
    return StoryCategory.objects.all()


@register.assignment_tag
def get_stories_by_category(category_slug, limit=5):
    return Story.objects.published().filter(category__slug__exact=category_slug)[:limit]


@register.assignment_tag
def get_stories_latest(limit=5):
    return Story.objects.published()[:limit]
