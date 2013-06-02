# coding: utf-8
from .api import Redmine
import httpretty


@httpretty.activate
def test_api_wrapper():
    httpretty.register_uri(httpretty.GET,
                           "http://example.com/groups.json",
                           responses=[
                               httpretty.Response('{"groups":[{"id":1, "name":"Pokemon"}], "total_count": 2, "offset": 0, "limit": 1}'),
                               httpretty.Response('{"groups":[{"id":2, "name":"Robochicken"}], "total_count": 2, "offset": 1, "limit": 1}'),
                           ],
                           content_type="application/json")
    api = Redmine('http://example.com', 'ThisIsMyToken')
    entries = api.groups()

    assert list(entries) == [{'id': 1, 'name': 'Pokemon'}, {'id': 2, 'name': 'Robochicken'}]
    assert httpretty.HTTPretty.last_request.querystring == {'limit':['1'], 'offset': ['1']}