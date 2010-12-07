# coding:utf-8

"""
    glue plugin between pylucid <-> django-weave
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from pylucid_project.apps.pylucid.decorators import render_to

from pylucid_project.external_plugins.weave.models import Wbo


def absolute_uri(request, view_name, **kwargs):
    url = reverse(view_name, kwargs=kwargs)
    absolute_uri = request.build_absolute_uri(url)
    return absolute_uri


@login_required
@render_to("pylucid_weave/info_page.html")
def info_page(request):
    summary_info = []

    users = User.objects.all().values_list('id', 'username')
    for user_id, username in users:
        queryset = Wbo.objects.filter(user=user_id)

        count = queryset.count()

        try:
            latest = queryset.only("modified").latest("modified").modified
        except Wbo.DoesNotExist:
            # User hasn't used sync, so no WBOs exist from him
            latest = None
            oldest = None
        else:
            oldest = queryset.only("modified").order_by("modified")[0].modified

        summary_info.append({
            "username": username,
            "count": count,
            "latest_modified": latest,
            "oldest_modified": oldest,
        })

    context = {
        "title": "weave testproject url info",
        "summary_info": summary_info,
        "server_url": request.build_absolute_uri(),
        "register_check_url": absolute_uri(request, "weave-register_check", username=request.user.username),
        "info_url": absolute_uri(request, "weave-info", version="1.0", username=request.user.username),
    }
    return context
