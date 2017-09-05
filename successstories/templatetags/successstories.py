from django import template

from ..models import Story, StoryCategory


register = template.Library()


@register.simple_tag
def get_story_categories():
    return StoryCategory.objects.all()


@register.simple_tag
def get_featured_story():
    return Story.objects.random_featured()


@register.simple_tag
def get_stories_by_category(category_slug, limit=5):
    return Story.objects.published().filter(category__slug__exact=category_slug)[:limit]


@register.simple_tag
def get_stories_latest(limit=5):
    return Story.objects.published()[:limit]
