# coding: utf-8


class ImproperlyConfigured(Exception):
    """ Something wrong with config file
    """


class CustomFieldNotPresent(Exception):
    pass


class StopPollingApi(Exception):
    pass
