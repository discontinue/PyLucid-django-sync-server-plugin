# coding: utf-8

import time
import datetime
import traceback

try:
    import json # New in Python v2.6
except ImportError:
    from django.utils import simplejson as json

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.

from django import http
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied

from pylucid_project.apps.pylucid.decorators import check_permissions

from pylucid_project.pylucid_plugins.weave.models import Collection, Wbo


def _timestamp():
  # Weave rounds to 2 digits and so must we, otherwise rounding errors will
  # influence the "newer" and "older" modifiers
  return round(time.time(), 2)


def _datetime2epochtime(dt):
    assert isinstance(dt, datetime.datetime)
    timestamp = time.mktime(dt.timetuple()) # datetime -> time since the epoch
    # Add microseconds. FIXME: Is there a easier way?
    timestamp += (dt.microsecond / 1000000.0)
    return round(timestamp, 2)


def _debug_request(request):
    print "request.META['CONTENT_LENGTH']: %r" % request.META['CONTENT_LENGTH']
    print "request.GET: %r" % request.GET
    print "request.POST: %r" % request.POST
    print "request.FILES: %r" % request.FILES
    print "request.raw_post_data: %r" % request.raw_post_data


def assert_username(debug=False):
    """ Check if the username from the url is logged in. """
    def _inner(view_function):
        @wraps(view_function)
        def _check_user(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated():
                msg = "Permission denied for anonymous user. Please log in."
                request.page_msg.error(msg)
                raise PermissionDenied(msg)

            username = kwargs["username"]
            if user.username != username:
                msg = "Wrong user!"
                if debug:
                    msg += " (%r != %r)" % (user.username, username)
                request.page_msg.error(msg)
                raise PermissionDenied("Wrong user!")

            return view_function(request, *args, **kwargs)
        return _check_user
    return _inner



def json_response(debug=False):
    """ return a dict as a json string """
    def renderer(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            data = function(request, *args, **kwargs)

            if not isinstance(data, dict):
                msg = (
                    "renter_to info: %s has not return a dict, has return: %r (%r)"
                ) % (function.__name__, type(data), function.func_code)
                raise AssertionError(msg)

            try:
                data_string = json.dumps(data, sort_keys=True)
            except Exception, err:
                print traceback.format_exc()
                raise

            response = http.HttpResponse(data_string,
#                content_type='application/json'
                content_type='text/plain'
            )
            response["X-Weave-Timestamp"] = _timestamp()

            if debug:
                print "render debug for %r:" % function.__name__
                print "data: %r" % data
                print "response.content:", response.content
#                request.page_msg("render debug for %r:" % function.__name__)
#                request.page_msg("data: %r" % data)
#                request.page_msg("response.content:", response.content)

            return response
        return wrapper
    return renderer




def root_view(request):
    print "root_view!"
    _debug_request(request)

    return "weave plugin, use this url: %s" % request.build_absolute_uri()



@assert_username(debug=True)
@check_permissions(superuser_only=False, permissions=(u'weave.add_collection', u'weave.add_wbo'))
@json_response(debug=True)
def info_collections(request, version, username):
    """
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#GET
    """
    print "info_collections:"
    _debug_request(request)

    """
    GET
parse_url: '/1.0/u/info/collections'
status: '200 OK'
headers: [('Content-type', 'application/json'), ('X-Weave-Timestamp', '1265104735.8')]
content: '{"meta": "1265104735.79"}'
*** collections:
{'meta': {'global': '{"id": "global", "modified": 1265104735.79, "payload": "{\\"syncID\\":\\"l9SgOxeN7U\\",\\"storageVersion\\":\\"1.0\\"}"}'},
 'timestamps': {'meta': '1265104735.79'}}
    """
    user = request.user

    collection_qs = Collection.on_site.filter(user=user)
    wbos = Wbo.objects.all().filter(collection__in=collection_qs).values("wboid", "lastupdatetime")

    timestamps = {}
    for wbo in wbos:
        lastupdatetime = wbo["lastupdatetime"]
        timestamp = _datetime2epochtime(lastupdatetime) # datetime -> time since the epoch
        timestamps[wbo["wboid"]] = str(timestamp)

    print timestamps

    return timestamps



@assert_username(debug=True)
@check_permissions(superuser_only=False, permissions=(u'weave.add_collection', u'weave.add_wbo'))
@json_response(debug=True)
def storage(request, version, username, col_name, wboid):
    """
request contents: '{"id":"global","payload":"{\\"syncID\\":\\"-Q0iwD4ysI\\",\\"storageVersion\\":\\"1.0\\"}"}'
PUT: '/1.0/1/storage/meta/global'
*** /1.0/1/storage/meta/global
debug collections:
{'meta': {'global': '{"id": "global", "modified": 1265101922.3499999, "payload": "{\\"syncID\\":\\"-Q0iwD4ysI\\",\\"storageVersion\\":\\"1.0\\"}"}'},
 'timestamps': {'meta': '1265101922.35'}}
 
 {'crypto': {'clients': '{"id": "clients", "modified": 1265103194.97, "payload": "{\\"bulkIV\\":\\"UGpwA/Eccf8YgZtz7enIPg==\\",\\"keyring\\":{\\"http://192.168.7.20:8000/1.0/1/storage/keys/pubkey\\":\\"oGc6jxv576JAFViewbYR1T2Q8WVCPNFUGXqn+Y+2aylIIqrDnF5zT2ZesrduwHlYrNud4s6+YfX3r7u72H9roAS0tBt0uEaeRkXBQ8Z62rmdkbYkOTc62gZ6+14lmoAJZSvjRPpRSxg0WAKREPYAkDs+ShNRSoW6q2itEi0mvPoVhdiCMMdvOfn2viKvsqys2tmIIytD7EqVugFUqrtch/4TBVNCkpMRbQvwrwnQrXujsZmUFfpElFvGtVxecEe5KeVIMXPZur+itMDtRaxgtXmGOu8pj/+giQ2SOZEiGwQmB2Q95lKZ/l8f+xtKWdyAQPCXcigb/a1A4eA0QO6+sw==\\"}}"}'},
 'keys': {'privkey': '{"id": "privkey", "modified": 1265103194.9400001, "payload": "{\\"type\\":\\"privkey\\",\\"salt\\":\\"4eejo7R/ee5FbGK8Ya9BzQ==\\",\\"iv\\":\\"7b3KhcFkULWjCHyBL8C3Nw==\\",\\"keyData\\":\\"3UyCkSOvjjh80cv/i+8kOI5fqGwWlHvaO0ZUXgAGkmb6QeNdJ53krrMGQ2qKIZ3rFk2xPPLagdY1SJBRWgzXp4kiRMp7PheBmULUhvW/IQKfO4Zz3DjAW/B7dbsfjSFsFOzVookdCdYVkDFk2f35YdvVTeUI0M0iNJDo9uSDldGC1z5CLGbOcFav8BdnK3TuCh3JNnG90uNBc4TT2bdWTmZdtjQLFSnude+LQHOSBKrX+sNA9EMyj5YhaS2PXfHwQPT6g2geo3F4Ah1KrY5wB1P3f7wdr2vCYpyC38YeNYjy5kxaoKHhFQXzHqgkw3+3V44wRYH9ajdh2XMKZrJOn1n7LUBn0/E9PwmmczqBgUOeGkRWhSFBOWGXfbzMnwQHtu6YEzvQdQd0qwkMX0dl65etex93FNNi5jXm4DRPiO1mOce39VyAXl+j/b/zZ2RKfBeF9f2yfqZxS8aqCcYLVGf8uz+YdfwgrHWtRlaqwXBL+p9Wk8yaxed0phQO4yHBzdm4Fks5qchMWXK1EIKkv75VzjzNfEo+z6r0EfRkqDJ3/Yt1tX258QXnt96RCNT01RLyp80Uw4+CIu0q4680/zANehwB5fR3QRgA5WNJk5ZCTMp4FbfxckM1us7W/iaJpIKmq0UssMaD8OaP9peUbOAQwN+/JQqttq/K/8+MO0I3B6tvoqx2YB9n/06Bp9qgQgvZXVbjDyJr8I8PS8Sh2/ahbb9mzubNc8kHwhFfFgAZ68Zv36oYFkbw2hKCmG8nuWZccUYOf7MwceINyfJaqXxMljmPdH/L0DxoZs0e4zrswUmDDZzVwSifMq6l8wbxWDT8Lpx7HP2wJTnGzmVAUSM4bLLRIVKZA+zohpDc0g3MpOg+h0m2LaUZucDoQLQv87HEV3S/66WC69vG+YaRFx99a0BeuASWBWgxrd0xFSMujZqw/s2eYp8a9eJQRzYf+F3Qh73+E6049oqyiwz0CZhBtup1bfXD2WTlGXD8Y28ELbbilgi4gPrP4qvFmJ8FHlZaM2xD6xiGnOlN0OrtcMRYi94Rec2IJUTdJPYl+b+VeUUZ/k6i4GtrRPMCWw0pQa0t3Q3VX/OJbaI6amReVeysw3A3e9gBSY7okGVeKen/CH+FbnQQfTTktxULHG1K1EwaP0p6RV1lSb1rTUrB7psfe3Kc0FTzS2TB+JWV5ovjfVFmEnS0lAiBiW4nDMXXTd+TursqJVddlJep0pW1x5rpg9B5weoGrHxFTtKKE6oNLP3uG+djvkLOA9mTdCJ+ntj1QjbE+QfNqtGSFLlopiV62cd2SjiYBToQ0iKHkFplEH8lXghMJXbC/4B7LibSWNLC8N58j6F9lRZd5JMaL2QmZWzxoBTpWegfuoFiuzrUWHqxjcEsP7Fi6wQIV0jhf9mSw4dhc4sEGD7ry3l/h9kNQt6hgdICRqUKb+LTvseboKWeansmDR/Xzg1MVyXC9YZrikGYWAHhjyijN0yWHccED3UPqkOJ9jtz95HjkB6GlIFL9cVKfrx7AGHnzcijv4xpJPJ0AQVz6b9maBN9AU7UtjYJt4ZSVlVzj8qiKi9o4V8BoFGxCsBVpisFST5tDkhS1IulAPpIhgzJjheEO1ZtexJap9qw+lsd+EoBzig=\\",\\"publicKeyUri\\":\\"http://192.168.7.20:8000/1.0/1/storage/keys/pubkey\\"}"}',
          'pubkey': '{"id": "pubkey", "modified": 1265103194.9300001, "payload": "{\\"type\\":\\"pubkey\\",\\"keyData\\":\\"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAseRPHJfRjolftNwdjH2MzEaVlG2tFYbxLFP6S8n2Yg9EYB7rOyvkm/TXE4ohkoxRLqxDCoLGhB4XLeYk5e4Rct8t3muyv/e3QH5meAqP9/1LJSkuWD+h6oLWSAXsrfl7uNsONUci+6WgC6HNqkwDgACKIHSfLwW78+yLvy+zAtb4EMzHRYBqQ6aHZ78DWDVvymmlhABedUZThaCcJqD9SVnjv5SVycLjN37ZmmBIXHEtGVChYhDynPXOjouuZa06FF6Vtpy9BsWcjh22eAsbHn8HYxXX+tHPLh3nh0Gbmhz1uQMyIBVt7Gv+ipOpn70kFJU7LwqJpka9kPAX6o4lSwIDAQAB\\",\\"privateKeyUri\\":\\"http://192.168.7.20:8000/1.0/1/storage/keys/privkey\\"}"}'},
 'meta': {'global': '{"id": "global", "modified": 1265103193.99, "payload": "{\\"syncID\\":\\".WFFECeqqU\\",\\"storageVersion\\":\\"1.0\\"}"}'},
 'timestamps': {'crypto': '1265103194.97',
                'keys': '1265103194.94',
                'meta': '1265103193.99'}}
    """
    print "storage", col_name, wboid
    _debug_request(request)

    user = request.user

    if request.method == 'PUT':
        # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#PUT
        # Adds the WBO defined in the request body to the collection.

        payload = request.raw_post_data
        if not payload:
            # If the WBO does not contain a payload, it will only update
            # the provided metadata fields on an already defined object.
            raise NotImplemented

        val = json.loads(payload)
        assert val["id"] == wboid, "wrong wbo id: %r != %r" % (val["id"], wboid)

        collection, created = Collection.on_site.get_or_create(user=user, name=col_name)
        if created:
            print "Collection %r created" % collection
        else:
            print "Collection %r exists" % collection

        sortindex = val.get("sortindex", None)

        wbo = Wbo(
            collection=collection,
            wboid=wboid,
            sortindex=sortindex,
            payload=payload
        )
        wbo.save()

        # The server will return the timestamp associated with the modification.
        data = {wboid: _datetime2epochtime(wbo.lastupdatetime)}
        return data
    elif request.method == 'GET':
        # Returns a list of the WBO ids contained in a collection.
        try:
            collection = Collection.on_site.get(user=user, name=col_name)
        except Collection.DoesNotExist:
            raise http.Http404

        wbos = Wbo.objects.all().filter(collection=collection)
        print "+++", wbos
        timestamps = {}
        for wbo in wbos:
            lastupdatetime = wbo.lastupdatetime
            timestamp = _datetime2epochtime(lastupdatetime) # datetime -> time since the epoch
            timestamps[wbo.wboid] = str(timestamp)

        print timestamps

        return timestamps
    else:
        raise NotImplemented


#request contents: '{"id":"global","payload":"{\\"syncID\\":\\"l9SgOxeN7U\\",\\"storageVersion\\":\\"1.0\\"}"}'
#PUT
#parse_url: '/1.0/u/storage/meta/global'
#status: '200 OK'
#headers: [('Content-type', 'text/plain'), ('X-Weave-Timestamp', '1265104735.79')]
#content: '200 OK'
#*** collections:
#{'meta': {'global': '{"id": "global", "modified": 1265104735.79, "payload": "{\\"syncID\\":\\"l9SgOxeN7U\\",\\"storageVersion\\":\\"1.0\\"}"}'},
# 'timestamps': {'meta': '1265104735.79'}}


    try:
        collection = Collection.on_site.get(user=request.user, name=col_name)
    except Collection.DoesNotExist:
        raise http.Http404("collection not found.")


    raw_post_data = request.raw_post_data
    if raw_post_data:
        print "raw_post_data: %r" % raw_post_data
        val = json.loads(raw_post_data)
        print "val1: %r" % val
        val['modified'] = _timestamp()
        print "val2: %r" % val
        val = json.dumps(val, sort_keys=True)

#        self.collections.setdefault(col, {})[key] = val
#        self.ts_col(col)


    response = http.HttpResponse("{}", content_type='application/json')
    response["X-Weave-Timestamp"] = _timestamp()
    return response


def sign_in(request, version, username):
    print "sign_in %r" % username
    print "request.user: %r" % request.user
    _debug_request(request)
    raise http.Http404


def exist_user(request, version, username):
    """
    https://wiki.mozilla.org/Labs/Weave/User/1.0/API
    Returns 1 if the username is in use, 0 if it is available. 
    """
    print "exist_user:"
    _debug_request(request)

    exist = User.objects.get(username=username).count()
    if exist:
        response_content = "1"
    else:
        response_content = "0"

    response = http.HttpResponse(response_content, content_type='application/json')
    response["X-Weave-Timestamp"] = _timestamp()
    return response

def captcha_html(request, version):
    print "captcha_html:"
    _debug_request(request)

#    raise http.Http404
    #response = http.HttpResponse("11", status=400, content_type='application/json')
    response = http.HttpResponse("not supported")
    response["X-Weave-Timestamp"] = _timestamp()
    return response


def setup_user(request, version, username):
    print "setup_user", version, username
    _debug_request(request)

    absolute_uri = request.build_absolute_uri()

    response = HttpResponse("{}", content_type='application/json')
    response["X-Weave-Timestamp"] = _timestamp()
    return response

