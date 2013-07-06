# coding: utf-8
from UserDict import UserDict
from collections import namedtuple
from redmine_alerts.api import Redmine


class AlreadyProcessed(Exception):
    pass


class Memo(UserDict):

    def __getitem__(self):
        pass
        # read from file

    def __setitem__(self):
        # write to file
        pass


def main():
    """ Here goes """
    config = namedtuple()
    api = Redmine.api(config.redmine.url, config.redmine.api_token)
    api.latest_processed_entry_id = Memo()

    for time_entry in api.time_entries():
        try:
            if should_process(time_entry):
                # process
        except AlreadyProcessed:
            break

    # Get latest time entries
    # Check, if issue is monitored
    #   (estimated_hours not set or issue already processed, or alert has been sent, for set of projects)
    # Get actual spent time for issue (taking into account activity type, nested tasks)
    # Check if notification needs to be sent
    # Get concerned parties emails
    # Notify them right away


    # Make extensive logs
    # If subissue has not estimate, check against parent estimate






def should_process(time_entry):
    """ Check, if issue needs processing

        * issue is not already processed
        * estimated_hours is set
        * alert has not been sent
        * issue is not excluded from query
    """

    # issue is not already processed
    # TODO: GH-1 Workaround time_entries sorting
    if time_entry['id'] <= api.latest_processed_entry_id:
        raise AlreadyProcessed()

    issue = api.issues(time_entry['issue_id']).GET(params={'include': 'children'})
    estimate =  or issue['parent']['id']

    # allowed_activities_ids    = config.redmine.activities

    return False