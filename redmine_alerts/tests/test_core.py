# coding: utf-8
import codecs
from os.path import abspath, join, dirname
from mock import patch
from redmine_alerts.core import watcher
from redmine_alerts.yml import AttrDict
from .fixtures import httpretty


path_to_yml = abspath(join(dirname(__file__), 'config', 'alerts.yml'))
path_to_json = abspath(join(dirname(__file__), 'json'))


@patch('redmine_alerts.plugins.SMTPPlugin.send')
def test_sanity_of_watcher(outbox, httpretty):

    # It's not possible to use both httpretty and pytest-localserver together
    # Httpretty patches socket module, so local smtp server won't be reached
    # Httpretty can't be easlity eliminated, because we need to make at lest 2 http requests
    # TODO: replace mock.patch with real smtp server mock

    httpretty.register_uri(httpretty.GET,
                           "https://example.com/time_entries.json?limit=100&offset=0",
                           body=codecs.open(join(path_to_json, 'time_entries.json')).read(),
                           content_type="application/json")
    httpretty.register_uri(httpretty.GET,
                           "https://example.com/issues/14221.json?include=children",
                           body=codecs.open(join(path_to_json, 'issues_14221.json')).read(),
                           content_type="application/json")
    config = AttrDict.from_yaml(path_to_yml)  # TODO: fixture
    watcher(config)
    assert outbox.call_count == 1
