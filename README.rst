Redmine alerts
--------------

Notify developers and managers when spent time reached estimate on task in `Redmine`_.

.. note::
    This is work in progress. Alerts are not finished.

Installation
~~~~~~~~~~~~

Redmine alerts should work with Redmine 1.1+::

    pip install redmine-alerts

Configure settings (see below).

Add custom boolean field to issues. It's required to track sent emails.

Add to cron::

    redmine-alerts

Configuration
~~~~~~~~~~~~~

Sample config file in yaml.
Feel free to omit most of the settings, the script will tell you if anything is missing.
Example of configuration::

    ~/.alertsrc
    redmine:
        url: https://example.com
        api_key: 018e918331a0798bd70fae73e6dd06961b1f0697
    overtime:
        alert_field_id: 12  # ID of boolean custom-field
        projects:  # skip this item to enable for every project
            - id: 42
              notify:
                - manager1@company.org
                - manager2@company.org
        activities:
            - 1  # development
            - 2  # another activity_id
        spent_notify_ratio: 110%  # % the percentage of time exceeded
        notify:  # for all projects
            - director@company.org
        subject: "[{issue.project.name}] Time exceeded on #{issue.id} {issue.subject}"
        message_template: redmine_alerts/templates/email_template.html
    email:
        host: "smtp.localhost"
        user: user
        password: password
        port: 25
        mode: SSL

How it works
~~~~~~~~~~~~

The script hits Redmine API, querying most recent `time_entries`_ since last fetch.
For each new time interval it finds a corresponding issue and checks
if time spent on issue has reached the estimated time. In that case the assignee
is notified via email that he is now behind the schedule.

You can customize:

* who else receives email when time limit is exceeded (``notify``)
* how much time needs to be spent to trigger notification (``spent_notify_ratio=100%``)


Development
~~~~~~~~~~~
::

    python setup.py test


.. _Redmine: http://www.redmine.org/
.. _time_entries: http://www.redmine.org/projects/redmine/wiki/Rest_TimeEntries
