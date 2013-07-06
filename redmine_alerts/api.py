# coding: utf-8
from decimal import Decimal
from hammock import Hammock
import six


class RestApiWithGenerator(Hammock):
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

    def _url(self, *args):
        return super(RestApiWithGenerator, self)._url(*args) + '.json'

    def _request(self, method, *args, **kwargs):
        single_attr = kwargs.pop('single_attr', None)
        if method == 'get' and not single_attr:
            return self._paginator(method, self._url(*args), **kwargs)
        else:
            return self._session.request(method, self._url(*args), **kwargs).json()[single_attr]

    def _paginator(self, method, uri, **kwargs):
        kwargs.setdefault('params', {})
        offset = kwargs['params'].get('offset', 0)
        limit = kwargs['params'].get('limit', 100)
        while uri and offset is not None:
            api_items, offset = self._page_request(method, uri, limit=limit, offset=offset, **kwargs)
            for item in api_items:
                yield item

    def _page_request(self, method, uri, limit, offset, **kwargs):
        kwargs['params'].update({'limit': limit, 'offset': offset})
        response = self._session.request(method, uri, **kwargs).json()
        # in case it's not paginated result
        if not 'total_count' in response:
            return next(six.itervalues(response)), None
        objects = response[uri[:-5].rsplit('/')[-1]]  # http://example.com/users.json -> users
        next_offset = limit + offset
        if offset + limit < response['total_count']:
            return objects, next_offset
        else:
            return objects, None


class Redmine(object):

    def __init__(self, url, api_key):
        self.api = RestApiWithGenerator(url, headers={'Content-Type': 'application/json', 'X-Redmine-API-Key': api_key})

    def get_actual_estimate(self, issue):
        """ Get real estimate of an issue.

            If issue has its own estimate, return it.
            If issue does not have estimate, pull it from one of the parent tickets if any.
            Returns None if estimate is unknown.
        """
        if issue.get('estimated_hours'):
            return Decimal(str(issue['estimated_hours']))
        if issue.get('parent'):
            return self.get_actual_estimate(self.api.issues(issue['parent']['id']).GET(single_attr='issue'))
        return None

    def get_actual_spent_time(self, issue, activities_ids=None):
        """ Get real amount of time spent on issue.

            * Filter only activities marked as relevant in settings (all are ok by defalut)
            * Sum up spent_time for all subtasks

            Total by issue is filtered via /time_entries.json?issue_id=<issue_id>
            Info on subtasks are obtained via /issues/<issue_id>.json?include=children
            Unfortunately, has O(2(n+1)) requests per ticket, n - child tickets due to API limitations.
        """
        issue_time_entries = self.api.time_entries.GET(params={'issue_id': issue['id']})
        self_total_spent = sum((Decimal(str(entry['hours'])) for entry in issue_time_entries
                                if not activities_ids or entry['activity']['id'] in activities_ids))

        children_total_spent = sum(self.get_actual_spent_time(immediate_child)
                                   for immediate_child in issue.get('children', []))

        return self_total_spent + children_total_spent