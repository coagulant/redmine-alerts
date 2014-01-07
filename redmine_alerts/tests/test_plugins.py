from decimal import Decimal
import logging
from mock import patch, MagicMock
import pytest

from redmine_alerts.plugins import Overtime, Notification, SMTPPlugin
from redmine_alerts.yml import AttrDict
from .fixtures import *


@pytest.fixture
def overtime(redmine):
    return Overtime(redmine, AttrDict({'alert_field_id': 12}))


@pytest.fixture
def overtime_full(redmine):
    return Overtime(redmine, AttrDict.from_yaml('.alertsrc').overtime)


# assert overtime.should_process(already_processed)

def test_should_not_process_ignored_activity(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}, "activity": {"id": 15, "name": "Drink"}}]}',
                           content_type="application/json")

    overtime.config.activities = [14, 16]
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    assert '[skipped, activity]' in redminelog.records()[0].getMessage()


def test_should_not_process_missing_estimate(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "title": "Some issue"}}',
                           content_type="application/json")
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    assert '[skipped, estimate]' in redminelog.records()[0].getMessage()


def test_should_not_process_alert_already_sent(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "estimated_hours": 2, "custom_fields": [{"id": 12, "value": "1"}]}}',
                           content_type="application/json")
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    assert '[skipped, sent]' in redminelog.records()[0].getMessage()


def test_should_not_process_ignored_project(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "estimated_hours": 2, "project": {"id": 3}, "custom_fields": [{"id": 12}]}}',
                           content_type="application/json")

    overtime.config.projects = [{'id': 1}, {'id': 2}]
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    assert '[skipped, projects]' in redminelog.records()[0].getMessage()


def test_should_process(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "estimated_hours": 2, "custom_fields": [{"id": 12}]}}',
                           content_type="application/json")

    assert overtime.should_process(next(overtime.api.time_entries.GET()))


def test_issue_process_is_overtime(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"issue_id": 1, "hours": 3.14},'
                                                 '{"issue_id": 1, "hours": 2.71}]}', content_type="application/json")

    overtime_issue = {
        'id': 1,
        'estimate': Decimal('5'),
        'project': {
            'name': 'Project'
        }
    }
    assert overtime.check_overtime(overtime_issue)
    assert '[OVERTIME]' in redminelog.records()[-1].getMessage()


def test_issue_process_no_overtime(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"issue": {"id": 1}, "hours": 3.14},'
                                                 '{"issue": {"id": 1}, "hours": 2.71}]}', content_type="application/json")
    no_overtime_issue = {
        'id': 1,
        'estimate': Decimal('500'),
        'project': {
            'name': 'Project'
        }
    }
    assert not overtime.check_overtime(no_overtime_issue)
    assert '[OVERTIME]' not in redminelog.text()


def test_get_recipients(overtime, httpretty):
    httpretty.register_uri(httpretty.GET,
                           "http://example.com/users/2.json",
                           body='{"user":{"id": 2, "mail": "some@developer.org"}}',
                           content_type="application/json")

    overtime.config.notify = ['company@director.org']
    overtime.config.projects = [{'id': 42, 'notify': ['project@manager.org', 'team@lead.org']}]

    issue = {'id': 1, 'project': {'id': 42}, 'assigned_to': {'id': 2}}
    assert overtime.get_recipients(issue) == set(['project@manager.org', 'team@lead.org',
                                                  'company@director.org', 'some@developer.org'])

    overtime.config.projects = []
    assert overtime.get_recipients(issue) == set(['company@director.org', 'some@developer.org'])


def test_run(overtime_full, httpretty):
    """ Some kind of integration test"""
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           responses=[
                               httpretty.Response('{"time_entries":[{"issue": {"id": 1}, "hours": 12, "activity": {"id": 1}},'
                                                 '{"issue": {"id": 2}, "hours": 100, "activity": {"id": 1}}]}'),
                               httpretty.Response('{"time_entries":[{"hours": 12, "activity": {"id": 1}}]}'),
                               httpretty.Response('{"time_entries":[{"hours": 100, "activity": {"id": 1}}]}')],
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "estimated_hours": 10.5, "custom_fields": [{"id": 12}],'
                                           '"subject": "Hello, world", "project": {"id": 42, "name": "FOO"}}}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/2.json",
                           body='{"issue":{"id": 2, "estimated_hours": 80, "custom_fields": [{"id": 12}],'
                                           '"subject": "It works", "project": {"id": 42, "name": "FOO"}}}',
                           content_type="application/json")

    expected_notifications = [
        Notification(subject='[FOO] Time exceeded on #1 Hello, world',
                     message=open('redmine_alerts/tests/mail/example1.eml').read(),
                     recipients=set(['manager2@company.org', 'director@company.org', 'manager1@company.org'])),
        Notification(subject='[FOO] Time exceeded on #2 It works',
                     message=open('redmine_alerts/tests/mail/example2.eml').read(),
                     recipients=set(['manager1@company.org', 'manager2@company.org', 'director@company.org']))
    ]
    assert list(overtime_full.run()) == expected_notifications


@patch('redmine_alerts.tests.test_plugins.SMTPPlugin')
def test_smtp(plugin_mock):
    plugin = SMTPPlugin(AttrDict.from_yaml('.alertsrc').email)
    plugin.send('Hello', 'Dolly!\nYarr!', recipients=['admin@localhost'])
    plugin_mock.assert_called_once_with(AttrDict([('host', 'smtp.localhost'), ('user', 'user'), ('password', 'password'), ('port', 25), ('mode', 'SSL')]))
    plugin_mock().send.assert_called_once_with('Hello', 'Dolly!\nYarr!', recipients=['admin@localhost'])
