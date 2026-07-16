from django.db import migrations


def fix_volunteer_cta(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    try:
        page = Page.objects.get(path="psf/volunteer")
    except Page.DoesNotExist:
        return

    content = page.content
    if "psf-volunteers" not in content:
        return

    # Remove the broken CTA section about the psf-volunteers mailing list,
    # which was archived during the Mailman 2.1 -> Mailman 3 migration in
    # May 2025 and no longer exists.
    lines = content.split("\n")
    new_lines = []
    drop = False
    for line in lines:
        if "psf-volunteers" in line:
            drop = True
        if not drop:
            new_lines.append(line)
        elif "Sign up" in line or "sign up" in line:
            continue
        elif line.strip() == "":
            drop = False
            new_lines.append(line)

    new_content = "\n".join(new_lines).strip()
    if new_content != content:
        page.content = new_content
        page.save()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0004_alter_page_creator_alter_page_last_modified_by"),
    ]

    operations = [
        migrations.RunPython(fix_volunteer_cta, migrations.RunPython.noop),
    ]
