import re
from pathlib import Path

import yaml
from django.conf import settings
from django.test import SimpleTestCase


class IssueTemplateTestCase(SimpleTestCase):
    """Tests to validate GitHub issue templates."""

    def setUp(self):
        self.issue_template_dir = Path(settings.BASE) / ".github" / "ISSUE_TEMPLATE"

    def test_issue_templates_exist_and_are_valid_yaml(self):
        """Ensure issue template YAML files exist and are syntactically valid."""
        yml_files = list(self.issue_template_dir.glob("*.yml"))
        self.assertGreater(len(yml_files), 0, "No issue template YAML files found")

        for file_path in yml_files:
            content = file_path.read_text(encoding="utf-8")
            parsed = yaml.safe_load(content)
            self.assertIsInstance(parsed, dict, f"{file_path.name} did not parse into a valid YAML mapping")

    def test_cpython_documentation_template_links_use_yml(self):
        """Regression test for #3149: verify documentation issue links use .yml not .md."""
        template_files = ["BUG.yml", "DOCS.yml", "REQUEST.yml"]
        docs_url_pattern = re.compile(r"https://github\.com/python/cpython/issues/new\?[^)\s]+")

        for filename in template_files:
            file_path = self.issue_template_dir / filename
            self.assertTrue(file_path.exists(), f"{filename} does not exist")
            content = file_path.read_text(encoding="utf-8")

            # Must not contain the broken .md link
            self.assertNotIn(
                "template=documentation.md",
                content,
                f"{filename} contains invalid template=documentation.md link (should be .yml)",
            )

            # Must contain the valid .yml link
            self.assertIn(
                "template=documentation.yml",
                content,
                f"{filename} is missing expected template=documentation.yml link",
            )

            # Ensure every cpython documentation link found uses .yml
            for match in docs_url_pattern.findall(content):
                if "labels=docs" in match:
                    self.assertIn(
                        "template=documentation.yml",
                        match,
                        f"Found broken link in {filename}: {match}",
                    )
