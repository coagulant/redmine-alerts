# coding: utf-8
from hammock import Hammock


class Redmine(Hammock):
    """ Redmine API wrapper with generator for pagination handling

        Example usage:
            api = Redmine.api('http://example.com', 'ThisIsMyToken')

            >> groups = api.groups.GET()
            /groups.json
            >> entries = api.issues.GET(params={'query_id': '42'})
            /issues.json?query_id=42
            >> entry = api.issues('2').GET()
            /issues/2.json

        See reference of api: http://www.redmine.org/projects/redmine/wiki/Rest_api
    """

    @classmethod
    def api(cls, url, api_key):
        return cls(url, headers={'Content-Type': 'application/json', 'X-Redmine-API-Key': api_key})

    def _url(self, *args):
        return super(Redmine, self)._url(*args) + '.json'

    def _request(self, method, *args, **kwargs):
        if method == 'get':
            return self._paginator(method, self._url(*args), **kwargs)
        else:
            return self._session.request(method, self._url(*args), **kwargs)

    def _paginator(self, method, uri, **kwargs):
        offset, limit = 0, 1
        while uri and offset is not None:
            api_items, limit, offset = self._page_request(method, uri, limit=limit, offset=offset)
            for item in api_items:
                yield item

    def _page_request(self, method, uri, limit, offset, **kwargs):
        kwargs.setdefault('params', {})
        kwargs['params'].update({'limit': limit, 'offset': offset})
        response = self._session.request(method, uri, **kwargs).json()
        objects = response[uri[:-5].rsplit('/')[-1]]  # http://example.com/users.json -> users
        next_offset = limit + offset
        if offset + limit < response['total_count']:
            return objects, limit, next_offset
        else:
            return objects, None, None