import os
import re
from django.test import TestCase
from django.conf import settings


class TemplateIntegrityTest(TestCase):
    def test_no_scripts_block_override(self):
        """
        Verify that no template overrides the 'scripts' block without calling
        {{ block.super }}. Overriding 'scripts' without super() blocks jQuery
        and causes JS errors.
        """
        template_dirs = [os.path.join(settings.BASE_DIR, "sm", "templates")]
        # Also check app templates
        for app in settings.INSTALLED_APPS:
            if not app.startswith("django."):
                app_path = os.path.join(
                    settings.BASE_DIR, app.split(".")[0], "templates"
                )
                if os.path.exists(app_path):
                    template_dirs.append(app_path)

        scripts_block_re = re.compile(r"{%\s*block\s+scripts\s*%}")
        block_super_re = re.compile(r"{{\s*block\.super\s*}}")

        errors = []
        for t_dir in template_dirs:
            for root, dirs, files in os.walk(t_dir):
                for file in files:
                    if file.endswith(".html"):
                        path = os.path.join(root, file)
                        # Skip base template itself
                        if "theme_bootstrap/base.html" in path:
                            continue

                        with open(path) as f:
                            content = f.read()
                            if scripts_block_re.search(content):
                                if not block_super_re.search(content):
                                    rel_path = os.path.relpath(path, settings.BASE_DIR)
                                    errors.append(
                                        f"{rel_path} overrides 'scripts' block"
                                        " without calling"
                                        " {{ block.super }}"
                                    )

        self.assertEqual(errors, [], "\n".join(errors))
