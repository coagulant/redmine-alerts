# coding: utf-8
import os
from redmine_alerts.yml import AttrDict


def test_yaml_attrdict():
    config = AttrDict.from_yaml(os.path.abspath('.alertsrc'))

    assert config.redmine.url == 'https://example.com'
    assert config.overtime.projects[0]['id'] == 42
    assert config.email.host == 'smtp.localhost'


def test_dump():
    config = AttrDict({'x': 'y', 'foo': ['bar', 'baz']})
    assert config.dump() == b'foo:\n- bar\n- baz\nx: y\n'