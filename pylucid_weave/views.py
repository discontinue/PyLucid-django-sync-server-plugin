# coding:utf-8

"""
    glue plugin between pylucid <-> django-weave
"""

import time

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from pylucid_project.apps.pylucid.decorators import render_to

from pylucid_project.external_plugins.weave.models import Wbo
from pylucid_project.external_plugins import weave



def absolute_uri(request, view_name, **kwargs):
    url = reverse(view_name, kwargs=kwargs)
    absolute_uri = request.build_absolute_uri(url)
    return absolute_uri


@login_required
@render_to("pylucid_weave/size_info.html")
def size_info(request, username):
    start_time = time.time()

    user_id = User.objects.get(username=username)
    queryset = Wbo.objects.filter(user=user_id).only("payload")

    wbo_count = 0
    payload_size = 0
    for item in queryset.iterator():
        wbo_count += 1
        payload_size += len(item.payload)

    duration = time.time() - start_time

    context = {
        "title": "Payload size",
        "username": username,
        "wbo_count": wbo_count,
        "payload_size": payload_size,
        "duration": duration,
    }
    return context



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
        "title": "django-sync-server info page",
        "summary_info": summary_info,
        "server_url": request.build_absolute_uri(),
        "weave_version": weave.VERSION_STRING,
        "register_check_url": absolute_uri(request, "weave-register_check", username=request.user.username),
        "info_url": absolute_uri(request, "weave-info", version="1.0", username=request.user.username),
    }
    return context
