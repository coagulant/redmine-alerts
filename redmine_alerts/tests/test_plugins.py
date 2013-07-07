import logging
import pytest

from redmine_alerts.plugins import Overtime
from redmine_alerts.yml import AttrDict
from .fixtures import *


@pytest.fixture
def overtime(redmine):
    return Overtime(redmine, AttrDict({'alert_field_id': 12}))


def test_should_not_process_ignored_activity(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}, "activity": {"id": 15, "name": "Drink"}}]}',
                           content_type="application/json")

    overtime.config.activities = [14, 16]
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    for record in redminelog.records():
        assert '[skipped, activity]' in record.getMessage()


def test_should_not_process_missing_estimate(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "title": "Some issue"}}',
                           content_type="application/json")
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    for record in redminelog.records():
        assert '[skipped, estimate]' in record.getMessage()


def test_should_not_process_alert_already_sent(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "estimated_hours": 2, "custom_fields": [{"id": 12, "value": "1"}]}}',
                           content_type="application/json")
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    for record in redminelog.records():
        assert '[skipped, sent]' in record.getMessage()


def test_should_not_process_ignored_project(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "estimated_hours": 2, "project": {"id": 3}, "custom_fields": [{"id": 12}]}}',
                           content_type="application/json")

    overtime.config.projects = [{'id': 1}, {'id': 2}]
    assert not overtime.should_process(next(overtime.api.time_entries.GET()))
    for record in redminelog.records():
        assert '[skipped, projects]' in record.getMessage()


def test_should_process(overtime, httpretty, redminelog):
    httpretty.register_uri(httpretty.GET, "http://example.com/time_entries.json",
                           body='{"time_entries":[{"id": 1, "issue": {"id": 1}}]}',
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET, "http://example.com/issues/1.json",
                           body='{"issue":{"id": 1, "estimated_hours": 2, "custom_fields": [{"id": 12}]}}',
                           content_type="application/json")

    assert overtime.should_process(next(overtime.api.time_entries.GET()))


# assert overtime.should_process(already_processed)
