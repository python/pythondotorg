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
            ['f1', 'created', 'updated', 'creator', 'last_modified_by']
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

    def test_get_fieldsets(self):
        admin = self.make_admin(fieldsets=[(None, {'fields': ['foo', 'created']})])
        fieldsets = admin.get_fieldsets(request=mock.Mock())

        # Check that "created" is removed from the specified fieldset and moved
        # into the automatic one.
        self.assertEqual(
            fieldsets,
            [(None, {'fields': ['foo']}),
             ('CMS metadata', {'fields': [('creator', 'created'), ('last_modified_by', 'updated')], 'classes': ('collapse',)})]
        )

    def test_save_model(self):
        admin = self.make_admin()
        request = mock.Mock()
        obj = mock.Mock()
        admin.save_model(request=request, obj=obj, form=None, change=False)
        self.assertEqual(obj.creator, request.user, "save_model didn't set obj.creator to request.user")

    def test_update_model(self):
        admin = self.make_admin()
        request = mock.Mock()
        obj = mock.Mock()
        admin.save_model(request=request, obj=obj, form=None, change=True)
        self.assertEqual(obj.last_modified_by, request.user, "save_model didn't set obj.last_modified_by to request.user")
