# coding: utf-8
"""Notify developers and managers when spent time reached estimate on task in Redmine.

Usage:
  redmine-alerts [options]

Options:
  -c FILE --config FILE     Specify where config file is [default: ~/.alertsrc]
  -h --help                 Show this screen.
  --version                 Show version.
"""
from docopt import docopt

import redmine_alerts
from redmine_alerts.core import watcher
from redmine_alerts.yml import AttrDict


def main():
    """ Here goes """
    arguments = docopt(__doc__, version=redmine_alerts.__version__)
    config = AttrDict.from_yaml(arguments['--config'])
    watcher(config)
