"""Forms for editing and publishing terms."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django import forms

from apps.agreements.forms.validation import _check_markdown, _check_placeholders
from apps.agreements.models import TermsVersion

if TYPE_CHECKING:
    from apps.agreements.models import Terms


class TermsForm(forms.Form):
    """Edit terms: save the working copy, or publish it as a new version."""

    SAVE = "save"
    PUBLISH = "publish"

    markdown = forms.CharField(
        label="Terms text",
        strip=False,
        widget=forms.Textarea(attrs={"rows": 30, "spellcheck": "true", "class": "markdown-editor"}),
        help_text="Markdown. Headings starting with '## ' become the contents list.",
    )
    under_review = forms.BooleanField(required=False, label="Draft for attorney review")
    is_public = forms.BooleanField(
        required=False,
        label="Make published versions public",
        help_text="Leave unchecked to restrict terms to staff and the parties to agreements that cite them.",
    )
    version = forms.SlugField(
        required=False,
        max_length=64,
        help_text="A new label for this version, for example today's date. Part of its permanent address.",
    )
    notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3}), help_text="What changed, for the version history."
    )
    action = forms.ChoiceField(choices=((SAVE, "Save draft"), (PUBLISH, "Publish")), required=False)

    def __init__(self, *args: Any, terms: Terms, can_publish: bool, **kwargs: Any) -> None:
        """Bind terms and expose publication fields only to administrators."""
        super().__init__(*args, **kwargs)
        self.terms = terms
        if not can_publish:
            for field in ("under_review", "is_public", "version", "notes"):
                del self.fields[field]
            cast("forms.ChoiceField", self.fields["action"]).choices = ((self.SAVE, "Save draft"),)

    def clean_markdown(self) -> str:
        """Normalize line endings; terms don't carry signature placeholders."""
        markdown: str = self.cleaned_data["markdown"].replace("\r\n", "\n")
        _check_placeholders(markdown, required=False)
        _check_markdown(markdown)
        return markdown

    def clean_is_public(self) -> bool:
        """Check visibility without changing the terms before the form is valid."""
        is_public: bool = self.cleaned_data["is_public"]
        self.terms.validate_is_public(is_public)
        return is_public

    def clean(self) -> dict[str, Any]:
        """Require a new version label, notes, and a change before publishing."""
        cleaned = cast("dict[str, Any]", super().clean())
        if cleaned.get("action") != self.PUBLISH:
            return cleaned
        version = cleaned.get("version")
        if not version:
            self.add_error("version", "Enter a label for the new version.")
        elif TermsVersion.objects.filter(terms=self.terms, version=version).exists():
            self.add_error("version", "This label is already used; published versions never change.")
        if not cleaned.get("notes", "").strip():
            self.add_error("notes", "Describe what changed.")
        current = self.terms.current_version
        if current and cleaned.get("markdown") == current.markdown:
            self.add_error("markdown", "The text is the same as the current version.")
        return cleaned
