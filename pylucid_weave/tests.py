#!/usr/bin/env python
# coding: utf-8

"""
    PyLucid unittests
    ~~~~~~~~~~~~~~~~~
    
    :copyleft: 2011 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

import os
import pprint
import base64

if __name__ == "__main__":
    # run all unittest directly
    os.environ['DJANGO_SETTINGS_MODULE'] = "pylucid_project.settings"

from django.conf import settings
from django.test.client import Client
from django.core.urlresolvers import reverse

from django_tools.unittest_utils.BrowserDebug import debug_response

from pylucid_project.tests.test_tools.basetest import BaseUnittest

from weave import app_settings as WEAVE_SETTINGS


class SyncTests(BaseUnittest):

    def _pre_setup(self, *args, **kwargs):
        super(SyncTests, self)._pre_setup(*args, **kwargs)

        # FIXME:
        settings.WEAVE = WEAVE_SETTINGS
        settings.DEBUG = True

        self.login("superuser")
        # Create the Plugin page
        new_plugin_page_url = reverse("PageAdmin-new_plugin_page")
        response = self.client.post(new_plugin_page_url,
            data={'app_label': 'pylucid_project.external_plugins.pylucid_weave',
            'design': 1,
            'position': 0,
            'slug': "sync",
            'urls_filename': 'urls.py'
            }
        )
        self.assertRedirect(response, "http://testserver/en/sync/", status_code=302)

        raw_auth_data = "superuser:superuser_password"
        self.auth_data = "basic %s" % base64.b64encode(raw_auth_data)

    def test_info_page(self):
        response = self.client.get("/en/sync/")
        self.assertResponse(response,
            must_contain=(
                '<title>PyLucid - django-sync-server - info page</title>',
                'Use <strong>http://testserver/en/sync/</strong> as server url',

                '<dt>WBO count</dt>', '<dd>0</dd>',
                '<dt>Payload size together</dt>', '<dd>0 bytes</dd>',
            ),
            must_not_contain=("Traceback",)
        )

    def test_if_installed(self):
        self.failUnless(
            'pylucid_project.external_plugins.weave' in settings.INSTALLED_APPS,
            "django-sync-server not in INSTALLED_APPS: %s" % pprint.pformat(settings.INSTALLED_APPS)
        )
        self.failUnless(
            'pylucid_project.external_plugins.pylucid_weave' in settings.INSTALLED_APPS,
            "PyLucid-django-sync-server-plugin not in INSTALLED_APPS: %s" % pprint.pformat(settings.INSTALLED_APPS)
        )

    def test_create_wbo(self):
        # Doen't work in PyLucid:
        #url = reverse("weave-col_storage", kwargs={"username":"testuser", "version":"1.1", "col_name":"foobar"})
        url = "/en/sync/1.1/superuser/storage/foobar"
        data = (
            u'[{"id": "12345678-90AB-CDEF-1234-567890ABCDEF", "payload": "This is the payload"}]'
        )
        response = self.client.post(url, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.auth_data)
        self.failUnlessEqual(response.content, u'{"failed": [], "success": ["12345678-90AB-CDEF-1234-567890ABCDEF"]}')
        self.failUnlessEqual(response["content-type"], "application/json")

    def test_csrf_exempt(self):
        # Doen't work in PyLucid:
        #url = reverse("weave-col_storage", kwargs={"username":"testuser", "version":"1.1", "col_name":"foobar"})
        url = "/en/sync/1.1/superuser/storage/foobar"

        data = (
            u'[{"id": "12345678-90AB-CDEF-1234-567890ABCDEF", "payload": "This is the payload"}]'
        )
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(url, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.auth_data)

        self.failUnlessEqual(response.content, u'{"failed": [], "success": ["12345678-90AB-CDEF-1234-567890ABCDEF"]}')
        self.failUnlessEqual(response["content-type"], "application/json")





if __name__ == "__main__":
    # Run all unittest directly
    from django.core import management

    tests = "external_plugins.pylucid_weave.tests"
#    tests = "external_plugins.pylucid_weave.tests.SyncTests.test_info_page"
#    tests = "external_plugins.pylucid_weave.tests.SyncTests.test_csrf_exempt"

    management.call_command('test', tests,
        verbosity=2,
#        verbosity=0,
#        failfast=True
    )
