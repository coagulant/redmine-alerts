# coding: utf-8
import logging
from redmine_alerts.cli import AlreadyProcessed

log = logging.getLogger('redmine-alerts')


class AlertPlugin(object):
    name = None

    def __init__(self, api, config):
        self.api = api
        self.config = config


class Overtime(AlertPlugin):

    def is_processed(self, time_entry):
        # TODO: GH-1 Workaround time_entries sorting
        #  if time_entry['id'] <= self.api.latest_processed_entry_id:
        return False

    def should_process(self, time_entry):
        """ Check, if time entry needs processing::

            1) issue is not already processed
            2) activity is involved in alert time tracking
            3) estimated_hours is set
            4) alert has not been sent
            5) issue is in tracked projects
        """

        # 1) issue is not already processed
        if self.is_processed(time_entry):
            raise AlreadyProcessed

        # 2) activity is involved in alert time tracking
        if 'activities' in self.config:
            if time_entry['activity']['id'] not in self.config.activities:
                log.debug('[skipped, activity] Time entry %s has activity %s, that is not in tracked %s',
                          time_entry['id'], time_entry['activity']['id'], self.config.activities)
                return False

        issue = self.api.issues(time_entry['issue']['id']).GET(params={'include': 'children'}, single_attr='issue')

        # 3) estimated_hours is set
        estimate = self.api.get_actual_estimate(issue)
        if not estimate:
            log.debug('[skipped, estimate] Issue #%s does not have estimate', issue['id'])
            return False

        # 4) alert has not been sent
        alert_is_sent = self.api.get_custom_field_value(issue, self.config.alert_field_id)
        if alert_is_sent:
            log.debug('[skipped, sent] Issue #%s has been notified already', issue['id'])
            return False

        # 5) issue is in tracked projects
        if 'projects' in self.config:
            monitored_projects = [project['id'] for project in self.config.projects]
            if issue['project']['id'] not in monitored_projects:
                log.debug('[skipped, projects] Issue #%s is not in monitored projects %s', issue['id'], monitored_projects)
                return False

        return True