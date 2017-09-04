from django import forms


class ContentManageableModelForm(forms.ModelForm):
    class Meta:
        fields = []

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)

        if self.request is not None and self.request.user.is_authenticated:
            if not obj.pk:
                obj.creator = self.request.user
            else:
                obj.last_modified_by = self.request.user

        if commit:
            obj.save()
        return obj
