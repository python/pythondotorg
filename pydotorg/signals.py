"""Signal handlers for sitetree cache invalidation."""

from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from sitetree.models import Tree, TreeItem
from sitetree.sitetreeapp import get_sitetree


@receiver(post_save, sender=Tree)
@receiver(post_save, sender=TreeItem)
@receiver(post_delete, sender=TreeItem)
@receiver(m2m_changed, sender=TreeItem.access_permissions)
def purge_sitetree_cache(sender, instance, **kwargs):
    """Purge sitetree cache on tree or item changes for cross-process invalidation."""
    cache_ = get_sitetree().cache
    cache_.empty()
    cache_.reset()
