"""Template tags for querying and displaying success stories in templates."""

from django import template

from successstories.models import Story, StoryCategory

register = template.Library()


@register.simple_tag
def get_story_categories():
    """Return all story categories."""
    return StoryCategory.objects.all()


@register.simple_tag
def get_featured_story():
    """Return a randomly selected featured success story."""
    return Story.objects.random_featured()


@register.simple_tag
def get_stories_by_category(category_slug, limit=5):
    """Return published stories filtered by category slug, up to the given limit."""
    return Story.objects.published().filter(category__slug__exact=category_slug)[:limit]


@register.simple_tag
def get_stories_latest(limit=5):
    """Return the most recently published stories, up to the given limit."""
    return Story.objects.published()[:limit]
