# coding: utf-8
import logging
import httpretty as http_pretty
import pytest

from redmine_alerts.api import Redmine


@pytest.fixture()
def httpretty(request):
    http_pretty.enable()
    http_pretty.HTTPretty.reset()
    request.addfinalizer(lambda: http_pretty.disable())
    return http_pretty


@pytest.fixture
def redmine():
    return Redmine('http://example.com', 'ThisIsMyToken')


@pytest.fixture
def redminelog(caplog):
    caplog.setLevel(logging.CRITICAL, logger='requests')
    caplog.setLevel(logging.DEBUG, logger='redmine-alerts')
    return caplog