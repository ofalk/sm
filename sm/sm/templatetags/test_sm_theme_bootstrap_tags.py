from django.test import TestCase
from django.contrib.messages import constants as DEFAULT_MESSAGE_LEVELS
from django.template import Context, Template

import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sm.settings'
django.setup()


class TestCase(TestCase):
    class FakeMessage(object):
        """
        Follows the `django.contrib.messages` API
        """
        level = None
        message = None
        extra_tags = None

        def __init__(self, level, message, extra_tags=None):
            self.level = level
            self.extra_tags = extra_tags
            self.message = message

    def test_00_load(self):
        string = '{% load sm_theme_bootstrap_tags %}'
        rendered = Template(string).render(Context({}))
        self.assertEqual(rendered, '')

    def test_01_warning(self):
        string = '{% load sm_theme_bootstrap_tags %}'
        string += '{% get_message_tags message %}'
        rendered = Template(string).render(Context({
            'message': TestCase.FakeMessage(DEFAULT_MESSAGE_LEVELS.WARNING,
                                            'warning message')
        }))
        self.assertEqual(rendered, 'alert-warning')

    def test_02_error(self):
        string = '{% load sm_theme_bootstrap_tags %}'
        string += '{% get_message_tags message %}'
        rendered = Template(string).render(Context({
            'message': TestCase.FakeMessage(DEFAULT_MESSAGE_LEVELS.ERROR,
                                            'error message')
        }))
        # error is danger in Bootstrap 3
        self.assertEqual(rendered, 'alert-danger')

    def test_02_warning_with_extra_tag(self):
        string = '{% load sm_theme_bootstrap_tags %}'
        string += '{% get_message_tags message %}'
        rendered = Template(string).render(Context({
            'message': TestCase.FakeMessage(DEFAULT_MESSAGE_LEVELS.WARNING,
                                            'message', 'testtag')
        }))
        self.assertEqual(rendered, 'testtag alert-warning')

    def test_03_extra_tag_only(self):
        string = '{% load sm_theme_bootstrap_tags %}'
        string += '{% get_message_tags message %}'
        rendered = Template(string).render(Context({
            'message': TestCase.FakeMessage(None, 'message', 'testtag')
        }))
        self.assertEqual(rendered, 'testtag')

    def test_04_empty(self):
        string = '{% load sm_theme_bootstrap_tags %}'
        string += '{% get_message_tags message %}'
        rendered = Template(string).render(Context({
            'message': TestCase.FakeMessage(None, '')
        }))
        self.assertEqual(rendered, '')
