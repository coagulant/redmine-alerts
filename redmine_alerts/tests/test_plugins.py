from decimal import Decimal
import logging
import pytest

from redmine_alerts.plugins import Overtime
from redmine_alerts.yml import AttrDict
from .fixtures import *


@pytest.fixture
def overtime(redmine):
    return Overtime(redmine, AttrDict({'alert_field_id': 12}))


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
    assert overtime.process(overtime_issue)
    assert '[OVERTIME]' in redminelog.records()[-1].getMessage()


def test_issue_process_no_overtime(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"issue_id": 1, "hours": 3.14},'
                                                 '{"issue_id": 1, "hours": 2.71}]}', content_type="application/json")
    no_overtime_issue = {
        'id': 1,
        'estimate': Decimal('500'),
        'project': {
            'name': 'Project'
        }
    }
    assert not overtime.process(no_overtime_issue)
    assert '[OVERTIME]' not in redminelog.text()