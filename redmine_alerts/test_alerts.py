# coding: utf-8
from decimal import Decimal
import httpretty
from .api import Redmine


@httpretty.activate
def test_api_wrapper_generator():
    httpretty.register_uri(httpretty.GET,
                           "http://example.com/groups.json",
                           responses=[
                               httpretty.Response('{"groups":[{"id":1, "name":"Pokemon"}], "total_count": 2, "offset": 0, "limit": 1}'),
                               httpretty.Response('{"groups":[{"id":2, "name":"Robochicken"}], "total_count": 2, "offset": 1, "limit": 1}'),
                           ],
                           content_type="application/json")
    redmine = Redmine('http://example.com', 'ThisIsMyToken')
    entries = redmine.api.groups.GET(params={'limit': 1})

    assert list(entries) == [{'id': 1, 'name': 'Pokemon'}, {'id': 2, 'name': 'Robochicken'}]
    assert httpretty.HTTPretty.last_request.querystring == {'limit': ['1'], 'offset': ['1']}


@httpretty.activate
def test_api_wrapper_single():
    httpretty.register_uri(httpretty.GET,
                           "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "title": "Some issue"}}',
                           content_type="application/json")
    redmine = Redmine('http://example.com', 'ThisIsMyToken')
    issue = redmine.api.issues(1).GET(single_attr='issue')

    assert issue == {"id": 1, "title": "Some issue"}


@httpretty.activate
def test_get_actual_estimate():
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"estimated_hours": 5}}', content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/2.json",
                           body='{"issue":{"parent":{"id": 3}}}', content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/3.json",
                           body='{"issue":{"estimated_hours": 2.5}}', content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/4.json",
                           body='{"issue":{"parent":{"id": 1}, "estimated_hours": 7}}', content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/5.json",
                           body='{"issue":{}}', content_type="application/json")
    redmine = Redmine('http://example.com', 'ThisIsMyToken')

    assert redmine.get_actual_estimate(redmine.api.issues('1').GET(single_attr='issue')) == Decimal(5), \
        'If issue has its own estimate, return it'
    assert redmine.get_actual_estimate(redmine.api.issues('2').GET(single_attr='issue')) == Decimal('2.5'), \
        'Pull estimate from parent'
    assert redmine.get_actual_estimate(redmine.api.issues('4').GET(single_attr='issue')) == Decimal(7),\
        'Own estimate is preferred'
    assert redmine.get_actual_estimate(redmine.api.issues('5').GET(single_attr='issue')) is None, \
        'No estimate'


@httpretty.activate
def test_get_actual_spent_time_no_filter():
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1}}', content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"issue_id": 1, "hours": 3.14}]}', content_type="application/json")

    redmine = Redmine('http://example.com', 'ThisIsMyToken')
    issue = redmine.api.issues('1').GET(single_attr='issue', params={'include': 'children'})

    assert redmine.get_actual_spent_time(issue) == Decimal('3.14'), \
        'Issue with no subissues, no activity filters'
    assert len(httpretty.HTTPretty.latest_requests) == 2
    assert httpretty.HTTPretty.latest_requests[-2].querystring == {'include': [u'children']}
    assert httpretty.HTTPretty.latest_requests[-1].querystring == {'issue_id': [u'1'], 'limit': [u'100'], 'offset': [u'0']}


@httpretty.activate
def test_get_actual_spent_time_filter():
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1}}', content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"issue_id": 1, "hours": 42, "activity": {"id": 5, "name": "dev"}},'
                                '{"issue_id": 1, "hours": 13, "activity": {"id": 7, "name": "test"}}]}',
                           content_type="application/json")

    redmine = Redmine('http://example.com', 'ThisIsMyToken')
    issue = redmine.api.issues('1').GET(single_attr='issue', params={'include': 'children'})

    assert redmine.get_actual_spent_time(issue, activities_ids=[7]) == Decimal(13), \
        'Issue with no subissues, activity filter by activity_id=7'


@httpretty.activate
def test_get_actual_spent_time_child_tasks():
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "children": [{"id": 2, "children": [{"id": 3}]}]}}', content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           responses=[
                               httpretty.Response('{"time_entries":[{"hours": 1}]}'),
                               httpretty.Response('{"time_entries":[{"hours": 2}]}'),
                               httpretty.Response('{"time_entries":[{"hours": 3}]}')],
                           content_type="application/json")

    redmine = Redmine('http://example.com', 'ThisIsMyToken')
    issue = redmine.api.issues('1').GET(single_attr='issue', params={'include': 'children'})

    assert redmine.get_actual_spent_time(issue) == Decimal(6), \
        'Issue with subissues, no filters'
    assert len(httpretty.HTTPretty.latest_requests) == 4
    assert httpretty.HTTPretty.latest_requests[-3].querystring == {'issue_id': [u'1'], 'limit': [u'100'], 'offset': [u'0']}
    assert httpretty.HTTPretty.latest_requests[-2].querystring == {'issue_id': [u'2'], 'limit': [u'100'], 'offset': [u'0']}
    assert httpretty.HTTPretty.latest_requests[-1].querystring == {'issue_id': [u'3'], 'limit': [u'100'], 'offset': [u'0']}