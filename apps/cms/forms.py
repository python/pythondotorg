"""Forms for content-manageable models."""

from django import forms


class ContentManageableModelForm(forms.ModelForm):
    """ModelForm that auto-sets creator and last_modified_by from the request user."""

    class Meta:
        """Meta configuration for ContentManageableModelForm."""

        fields = []

    def __init__(self, request=None, *args, **kwargs):
        """Initialize with an optional request for tracking the current user."""
        self.request = request
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Save the model, setting creator or last_modified_by from the request user."""
        obj = super().save(commit=False)

        if self.request is not None and self.request.user.is_authenticated:
            if not obj.pk:
                obj.creator = self.request.user
            else:
                obj.last_modified_by = self.request.user

        if commit:
            obj.save()
        return obj
