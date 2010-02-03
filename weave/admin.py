# coding: utf-8

"""
    PyLucid.admin
    ~~~~~~~~~~~~~~

    Register all PyLucid model in django admin interface.

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate$
    $Rev$
    $Author$

    :copyleft: 2008-2009 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.auth.admin import UserAdmin

from reversion.admin import VersionAdmin

from pylucid_project.apps.pylucid_admin.admin_site import pylucid_admin_site

from pylucid_project.pylucid_plugins.weave.models import Wbo, Collection



class WboAdmin(VersionAdmin):
    def payload_cutout(self, obj):
        MAX = 100
        payload = obj.payload
        if len(payload) > MAX:
            payload = payload[:MAX] + "..."
        return payload
    payload_cutout.short_description = "Payload cutout"
#    view_on_site_link.allow_tags = True

    list_display = ("id", "lastupdatetime", "user", "wboid", "parentid", "sortindex", "lastupdateby", "payload_cutout")
    list_display_links = ("wboid",)
    list_filter = ("user", "collection")
    date_hierarchy = 'lastupdatetime'
#    search_fields = ("headline", "content")

pylucid_admin_site.register(Wbo, WboAdmin)


class CollectionAdmin(VersionAdmin):
    """
    """
    list_display = ("id", "lastupdatetime", "user", "name", "lastupdateby")
    list_display_links = ("name",)
    list_filter = ("user", "createby", "lastupdateby",)
    date_hierarchy = 'lastupdatetime'
#    search_fields = ("headline", "content")

pylucid_admin_site.register(Collection, CollectionAdmin)
