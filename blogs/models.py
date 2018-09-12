import feedparser

from django.db import models
from django.conf import settings

from cms.models import ContentManageable


class BlogEntry(models.Model):
    """
    Model to store Blog entries from Blogger
    Specificially https://blog.python.org/
    Feed URL is defined in settings.PYTHON_BLOG_FEED_URL
    """
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    pub_date = models.DateTimeField()
    url = models.URLField('URL')
    feed = models.ForeignKey('Feed', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Blog Entry'
        verbose_name_plural = 'Blog Entries'
        get_latest_by = 'pub_date'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.url


class Feed(models.Model):
    """
    An RSS feed to import.
    """
    name = models.CharField(max_length=200)
    website_url = models.URLField()
    feed_url = models.URLField()
    last_import = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

class FeedAggregate(models.Model):
    """
    An aggregate of RSS feeds.

    These allow people to edit what are in feed-backed content blocks
    without editing templates.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(help_text="Where this appears on the site")
    feeds = models.ManyToManyField(Feed)

    def __str__(self):
        return self.name

class Translation(ContentManageable):
    """ Model to store blog translation links """
    name = models.CharField(max_length=100)
    url = models.URLField('URL')

    class Meta:
        verbose_name = 'Translation'
        verbose_name_plural = 'Translations'
        ordering = ('name', )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return self.url


class Contributor(ContentManageable):
    """ Blog Contributors """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='blog_contributor',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Contributor'
        verbose_name_plural = 'Contributors'
        ordering = ('user__last_name', 'user__first_name')

    def __str__(self):
        return self.user.get_full_name()

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    def get_display_name(self):
        if self.user.first_name or self.user.last_name:
            return """{} {}""".format(self.user.first_name, self.user.last_name)
        else:
            return self.user.username


class RelatedBlog(ContentManageable):
    name = models.CharField(max_length=100, help_text="Internal Name")
    feed_url = models.URLField('Feed URL')
    blog_url = models.URLField('Blog URL')
    blog_name = models.CharField(max_length=200, help_text="Displayed Name")
    last_entry_published = models.DateTimeField(db_index=True)
    last_entry_title = models.CharField(max_length=500)

    class Meta:
        verbose_name = 'Related Blog'
        verbose_name_plural = 'Related Blogs'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return self.blog_url

    def update_blog_data(self):
        """ Update our related blog data """
        d = feedparser.parse(self.feed_url)
        self.blog_name = d['feed']['title']
        self.blog_url = d['feed']['link']
        self.last_entry_published = d['feed']['updated_parsed']
        self.last_entry_title = d['entries'][0]['title']
        self.save()
