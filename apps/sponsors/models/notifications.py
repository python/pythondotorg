"""Email notification template models for sponsor communications."""

import re

from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count, Max
from django.template import Context
from django.utils import timezone

from apps.mailing.models import BaseEmailTemplate

SPONSOR_TEMPLATE_HELP_TEXT = (
    "<br>"
    "You can use the following template variables in the Subject and Content:"
    "  <pre>{{ sponsor_name }}</pre>"
    "  <pre>{{ sponsorship_level }}</pre>"
    "  <pre>{{ sponsorship_start_date }}</pre>"
    "  <pre>{{ sponsorship_end_date }}</pre>"
    "  <pre>{{ sponsorship_status }}</pre>"
)

_NAME_LEADING_YEAR_RE = re.compile(r"^\s*(\d{4})\b")
# A leading number outside this range is part of the name, not a year.
_PLAUSIBLE_YEARS = range(1901, 2100)


def year_from_name(name):
    """Return the leading 4-digit year parsed from a template name, or ``None``.

    Only a year at the very start of the name counts (prod names look like "2026 Final
    Sponsor Email"); years mentioned elsewhere in the name are intentionally ignored.
    """
    match = _NAME_LEADING_YEAR_RE.match(name or "")
    if not match:
        return None
    year = int(match.group(1))
    return year if year in _PLAUSIBLE_YEARS else None


# Historical sends recorded only as a Django admin LogEntry (before SponsorshipNotificationLog
# had a ``template`` FK) use this fixed message, written by notifications.SendSponsorNotificationLogger.
_LOG_ENTRY_MESSAGE_RE = re.compile(r"^Notification '(?P<name>.+)' was sent to contacts: ")


#################################
# Sponsor Email Notifications
class SponsorEmailNotificationTemplate(BaseEmailTemplate):
    """Configurable email template for sending notifications to sponsors."""

    class Meta:
        """Meta configuration for SponsorEmailNotificationTemplate."""

        verbose_name = "Sponsor Email Notification Template"
        verbose_name_plural = "Sponsor Email Notification Templates"
        ordering = ["-year", "internal_name"]

    year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Leave blank for an evergreen template usable across years.",
    )

    # Notifications go out as plain-text email, so values like "Code & Supply" must not be
    # HTML-escaped. The result is a plain str (not SafeString) so any HTML page that shows it,
    # such as a preview, escapes it and displays exactly what is sent.
    def _render_plain_text(self, source, context):
        template = self.template_engine.from_string(source)
        return str.__str__(template.render(Context(context, autoescape=False)))

    def render_content(self, context):
        """Render the email body as plain text."""
        return self._render_plain_text(self.content, context)

    def render_subject(self, context):
        """Render the email subject as plain text."""
        return self._render_plain_text(self.subject, context)

    def get_email_context_data(self, **kwargs):
        """Build template context from the sponsorship data."""
        sponsorship = kwargs.pop("sponsorship")
        context = {
            "sponsor_name": sponsorship.sponsor.name,
            "sponsorship_start_date": sponsorship.start_date or "",
            "sponsorship_end_date": sponsorship.end_date or "",
            "sponsorship_status": sponsorship.get_status_display(),
            "sponsorship_level": sponsorship.level_name,
        }
        context.update(kwargs)
        return context

    def get_email_message(self, sponsorship, **kwargs):
        """Build the email message for the given sponsorship and contact types."""
        contact_types = {
            "primary": kwargs.get("to_primary"),
            "administrative": kwargs.get("to_administrative"),
            "accounting": kwargs.get("to_accounting"),
            "manager": kwargs.get("to_manager"),
        }
        contacts = sponsorship.sponsor.contacts.filter_by_contact_types(**contact_types)
        if not contacts.exists():
            return None

        recipients = contacts.values_list("email", flat=True)
        return self.get_email(
            from_email=settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL,
            to=recipients,
            context={"sponsorship": sponsorship},
        )

    @classmethod
    def get_last_sent_stats(cls):
        """Return ``{template_id: {"last_sent": datetime, "sponsorship_count": int}}``.

        Combines two sources of truth, keeping the most recent per template:

        - ``SponsorshipNotificationLog`` rows with a ``template`` FK set — the reliable
          source for sends made since that field was added.
        - Admin ``LogEntry`` entries written by ``notifications.SendSponsorNotificationLogger``,
          matched by the template's ``internal_name`` against their fixed message format. This
          is the only record of sends made before the FK existed, so it is the fallback for
          historical data. Both lookups are single aggregated queries, not one per template.
          Renaming a template breaks the match for its pre-FK sends; that is an accepted
          limitation of reading an audit trail that only recorded the name as free text.
        """
        stats = {}

        fk_rows = (
            cls.objects.filter(notification_logs__isnull=False)
            .values("id")
            .annotate(
                last_sent=Max("notification_logs__sent_at"),
                sponsorship_count=Count("notification_logs__sponsorship", distinct=True),
            )
        )
        for row in fk_rows:
            stats[row["id"]] = {"last_sent": row["last_sent"], "sponsorship_count": row["sponsorship_count"]}

        ids_by_name = {}
        for template_id, name in cls.objects.values_list("id", "internal_name"):
            ids_by_name.setdefault(name, []).append(template_id)

        sponsorship_ct = ContentType.objects.filter(app_label="sponsors", model="sponsorship").first()
        if sponsorship_ct is None:
            return stats

        fallback = {}
        log_rows = LogEntry.objects.filter(
            content_type=sponsorship_ct,
            action_flag=CHANGE,
            change_message__startswith="Notification '",
        ).values_list("change_message", "action_time", "object_id")
        for message, action_time, object_id in log_rows:
            match = _LOG_ENTRY_MESSAGE_RE.match(message)
            if not match:
                continue
            name = match.group("name")
            entry = fallback.setdefault(name, {"last_sent": action_time, "sponsorship_ids": set()})
            entry["last_sent"] = max(entry["last_sent"], action_time)
            entry["sponsorship_ids"].add(object_id)

        for name, entry in fallback.items():
            for template_id in ids_by_name.get(name, ()):
                existing = stats.get(template_id)
                if existing is None or entry["last_sent"] > existing["last_sent"]:
                    stats[template_id] = {
                        "last_sent": entry["last_sent"],
                        "sponsorship_count": len(entry["sponsorship_ids"]),
                    }

        return stats


class SponsorshipNotificationLog(models.Model):
    """Persisted record of every notification sent to a sponsorship."""

    sponsorship = models.ForeignKey(
        "sponsors.Sponsorship",
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    template = models.ForeignKey(
        "sponsors.SponsorEmailNotificationTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
        help_text="The template this was sent from, if it was sent from a saved template.",
    )
    subject = models.CharField(max_length=500)
    content = models.TextField(blank=True)
    recipients = models.TextField(help_text="Comma-separated email addresses")
    contact_types = models.CharField(max_length=200, blank=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        """Meta configuration for SponsorshipNotificationLog."""

        ordering = ["-sent_at"]
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"

    def __str__(self):
        """Return a human-readable representation of the log entry."""
        return f"{self.subject} → {self.sponsorship} ({self.sent_at:%Y-%m-%d %H:%M})"

    # ``recipients`` stores To addresses bare and CC/BCC addresses as "cc: addr" / "bcc: addr".
    # A colon can't appear unquoted in an address, so the prefixes are unambiguous. Rows logged
    # before CC/BCC were tagged list every address bare, so they all read as To.
    COPY_PREFIXES = ("cc", "bcc")

    @classmethod
    def format_recipients(cls, to=(), cc=(), bcc=()):
        """Serialize recipients for the ``recipients`` field, tagging CC and BCC addresses."""
        return ", ".join([*to, *(f"cc: {addr}" for addr in cc), *(f"bcc: {addr}" for addr in bcc)])

    def _recipients_by_kind(self):
        """Split stored recipients into To, CC and BCC lists."""
        kinds = {"to": [], "cc": [], "bcc": []}
        for entry in filter(None, (raw.strip() for raw in self.recipients.split(","))):
            kind, sep, addr = entry.partition(":")
            kind = kind.strip().lower()
            if sep and kind in self.COPY_PREFIXES:
                kinds[kind].append(addr.strip())
            else:
                kinds["to"].append(entry)
        return kinds

    @property
    def recipient_list(self):
        """Return every recipient (To, CC and BCC) as a list of email addresses."""
        kinds = self._recipients_by_kind()
        return [*kinds["to"], *kinds["cc"], *kinds["bcc"]]

    @property
    def to_list(self):
        """Return the To addresses."""
        return self._recipients_by_kind()["to"]

    @property
    def cc_list(self):
        """Return the CC addresses."""
        return self._recipients_by_kind()["cc"]

    @property
    def bcc_list(self):
        """Return the BCC addresses."""
        return self._recipients_by_kind()["bcc"]

    @property
    def contact_type_list(self):
        """Return contact types as a list of strings."""
        return [t.strip() for t in self.contact_types.split(",") if t.strip()]
