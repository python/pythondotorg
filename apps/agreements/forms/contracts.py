"""Forms for custom contracts and agreement document revisions."""

from django import forms

from apps.agreements.documents import EFFECTIVE_DATE, SIGNATURES
from apps.agreements.forms.accounts import account_for_email
from apps.agreements.forms.validation import _check_markdown, _check_placeholders
from apps.agreements.models import CustomContract, Terms

MAX_NOTE_LENGTH = 255


class EditDocumentForm(forms.Form):
    """Edit one agreement's text before it is signed."""

    markdown = forms.CharField(
        label="Document text",
        strip=False,
        widget=forms.Textarea(attrs={"rows": 30, "spellcheck": "true", "class": "markdown-editor"}),
        help_text=f"Markdown. {SIGNATURES} marks the signature block and {EFFECTIVE_DATE} the effective date.",
    )
    note = forms.CharField(
        label="What changed and why",
        max_length=MAX_NOTE_LENGTH,
        help_text="Kept with the revision, for example: 'Net 45 payment terms, agreed with their counsel.'",
    )
    base_sha256 = forms.CharField(widget=forms.HiddenInput, max_length=64)

    def clean_markdown(self):
        """Normalize line endings and keep the signature placeholder."""
        markdown = self.cleaned_data["markdown"].replace("\r\n", "\n")
        _check_placeholders(markdown, required=True)
        _check_markdown(markdown)
        return markdown


class CustomContractForm(forms.ModelForm):
    """A one-off contract: who it is with, the text, and any terms it cites."""

    counterparty_account_email = forms.EmailField(
        required=False,
        label="Counterparty's python.org account",
        help_text="Email of the account that may sign online. Leave empty to email a signing link or "
        "collect a signed copy instead.",
    )

    class Meta:
        """Staff-editable fields; the signature block is added automatically."""

        model = CustomContract
        fields = ("title", "counterparty_name", "terms", "body_markdown")
        widgets = {"body_markdown": forms.Textarea(attrs={"rows": 24, "class": "markdown-editor"})}
        help_texts = {
            "body_markdown": "Markdown. The parties, any cited terms, and the signature block are added "
            "above and below this text."
        }

    def __init__(self, *args, can_link_accounts=False, **kwargs):
        """Offer only terms with a published version, and show the current account."""
        super().__init__(*args, **kwargs)
        self.fields["terms"].queryset = Terms.objects.filter(versions__isnull=False).distinct()
        self.can_link_accounts = can_link_accounts
        if can_link_accounts:
            account = self.instance.counterparty_account
            self.fields["counterparty_account_email"].initial = account.email if account else ""
        else:
            del self.fields["counterparty_account_email"]

    def clean_counterparty_account_email(self):
        """Resolve the email to exactly one account."""
        email = self.cleaned_data["counterparty_account_email"]
        return account_for_email(email) if email else None

    def clean_body_markdown(self):
        """Normalize line endings; placeholders are added automatically."""
        markdown = self.cleaned_data["body_markdown"].replace("\r\n", "\n")
        _check_placeholders(markdown, required=False)
        _check_markdown(markdown)
        return markdown

    def save(self, commit=True):
        """Store the resolved account."""
        if self.can_link_accounts:
            self.instance.counterparty_account = self.cleaned_data["counterparty_account_email"]
        return super().save(commit=commit)
