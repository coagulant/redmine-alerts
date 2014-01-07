# coding: utf-8
import logging
from .plugins import Overtime, SMTPPlugin
from .api import Redmine


def watcher(config):
    """ Core of alert system, does the whole work."""
    logger = logging.getLogger('redmine-alerts')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    try:
        api = Redmine(config.redmine.url, config.redmine.api_key)
        plugins = [Overtime(api, config.overtime)]
        messengers = [SMTPPlugin(config.email)]
    except KeyError as e:
        exit('Aborted. Missing config item %s' % e)

    for plugin in plugins:
        for notification in plugin.run():
            for messenger in messengers:
                messenger.send(notification.subject,
                               notification.message,
                               notification.recipients)
