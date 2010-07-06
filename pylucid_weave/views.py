# coding:utf-8

"""
    glue plugin between pylucid <-> django-weave
"""

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from pylucid_project.apps.pylucid.decorators import render_to


def absolute_uri(request, view_name, **kwargs):
    url = reverse(view_name, kwargs=kwargs)
    absolute_uri = request.build_absolute_uri(url)
    return absolute_uri


@login_required
@render_to("pylucid_weave/url_info.html")
def url_info(request):
    context = {
        "title": "weave testproject url info",
        "server_url": request.build_absolute_uri(),
        "register_check_url": absolute_uri(request, "weave-register_check", username=request.user.username),
        "info_url": absolute_uri(request, "weave-info", version="1.0", username=request.user.username),
    }
    return context
