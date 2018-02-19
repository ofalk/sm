"""
Extended wrapper for loading templates from app dirs.
Given server/list.html, will search in BASE_DIR/server/templates/list.html
"""

import os

from django.template import Origin

from django.template.loaders import filesystem
from sm.settings import BASE_DIR


class Loader(filesystem.Loader):

    def __init__(self, engine, dirs=None):
        super(Loader, self).__init__(engine)
        self.dirs = dirs

    def get_template_sources(self, template_name, template_dirs=None):
        """
        Return an Origin object pointing to an absolute path in application
        templates subdirectory.
        """
        # Only check if there's a directory separator
        # This might be a dirty hack
        separator = os.path.join('.', '')[-1]
        if separator in template_name:
            template_path = os.path.join(
                BASE_DIR,
                os.path.dirname(template_name),
                'templates',
                os.path.basename(template_name),
            )
            yield Origin(
                name=template_path,
                template_name=template_name,
                loader=self,
            )
