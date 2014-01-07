# coding: utf-8
import sys
from os.path import abspath, join, dirname
from mock import patch
from redmine_alerts.cli import main

path_to_yml = abspath(join(dirname(__file__), 'config', 'alerts.yml'))


@patch('redmine_alerts.cli.watcher')
@patch.object(sys, 'argv', new=['redmine-alerts', '--config', path_to_yml])
def test_sanity(watcher_mock):
    main()
    assert watcher_mock.called
