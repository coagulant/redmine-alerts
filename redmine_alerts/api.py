# coding: utf-8
from functools import partial
from hammock import Hammock


class Redmine(object):
    """ Redmine API wrapper with generator for pagination handling"""

    def __init__(self, url, api_key):
        self.api = Hammock(url, headers={'Content-Type': 'application/json', 'X-Redmine-API-Key': api_key})

    def __getattr__(self, name):
        return partial(self._paginator, '%s.json' % name)

    def _paginator(self, uri, method='GET', data=None):
        offset, limit = 0, 1
        while uri and offset is not None:
            api_items, limit, offset = self._request(uri, method, data, limit=limit, offset=offset)
            for item in api_items:
                yield item

    def _request(self, uri, method, data=None, limit=25, offset=0):
        api_call = getattr(self.api(uri), method)
        response = api_call(data=data, params={'limit': limit, 'offset': offset}).json()
        objects = response[uri.split('.')[0]]  # users.json -> users
        next_offset = limit + offset
        if offset + limit < response['total_count']:
            return objects, limit, next_offset
        else:
            return objects, None, None