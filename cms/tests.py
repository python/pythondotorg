import unittest
from unittest import mock
from .admin import ContentManageableModelAdmin

class ContentManagableAdminTests(unittest.TestCase):
    def make_admin(self, **kwargs):
        """
        Construct a dummy subclass of ContentManageableModelAdmin with
        attributes set per **kwargs.
        """
        cls = type("TestAdmin", (ContentManageableModelAdmin,), kwargs)
        return cls(mock.Mock(), mock.Mock())

    def test_readonly_fields(self):
        admin = self.make_admin(readonly_fields=['f1'])
        self.assertEqual(
            admin.get_readonly_fields(request=mock.Mock()),
            ['f1', 'created', 'updated', 'creator']
        )

    def test_list_filter(self):
        admin = self.make_admin(list_filter=['f1'])
        self.assertEqual(
            admin.get_list_filter(request=mock.Mock()),
            ['f1', 'created', 'updated']
        )

    def test_list_display(self):
        admin = self.make_admin(list_display=['f1'])
        self.assertEqual(
            admin.get_list_display(request=mock.Mock()),
            ['f1', 'created', 'updated']
        )

    def test_save_model(self):
        admin = self.make_admin()
        request = mock.Mock()
        obj = mock.Mock()
        admin.save_model(request=request, obj=obj, form=None, change=False)
        self.assertEqual(obj.creator, request.user, "save_model didn't set obj.creator to request.user")
