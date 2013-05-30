Redmine alerts
--------------

Notify developers and managers when spent time reached estimate on task in Redmine_.

Installation
~~~~~~~~~~~~

    pip install redmine-alerts

Configure settings (see below).

Add custom boolean field to issues. It's needed to track sent emails.

Add to cron::
    redmine-alerts

Configuration
~~~~~~~~~~~~~

Sample config file in yaml_.
Feel free to omit most of the settings, the script will tell you if anything is missing.

    # ~/.redminerc
    redmine:
        host: https://example.com
        api_key: 018e918331a0798bd70fae73e6dd06961b1f0697
        projects:  # skip this item to enable for every project
            - slug: my_super_project_codename
              notify:
                - manager1@company.org
                - manager2@company.org
        notify:
            - director@company.org
        activity:
            - 1 # development
            - 2 # another activity_id
        spent_notify: 90%  # % the percentage of time exceeded
        alert_field_id: 12 # ID of boolen custom-fiel
    email:
        host: smpt.company.org
        user: user
        password: password
        port: 25
        ssl: True

How it works
~~~~~~~~~~~~

The script hits Redmine API, querying latest `time_entries`_ since last fetch.
For each new logged interval it finds a corresponding issue and checks
if time spent has reached the estimated time. In that case the assignee
is notified via email that he is now behind the schedule.

You can customize:

    * who else recieves email when time limit is exceeded (`notify`)
    * how much time needs to be spent to trigger notification (`spent_notify`=100%)