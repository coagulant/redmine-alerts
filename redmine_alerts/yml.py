# coding: utf-8
"""
YAML-based configuration module.
Vendored and modified version of https://github.com/mk-fg/layered-yaml-attrdict-config

When you use resulting nested-dicts in code, consider the difference between
    config['core']['connection']['reconnect']['maxDelay'] and
    config.core.connection.reconnect.maxDelay.

Python dicts support only the first syntax, this module supports both.
Assigning values through attributes is also possible.
"""
import os
from collections import Mapping, defaultdict

try:
    from collections import OrderedDict
except ImportError:  # pragma: nocover
    from ordereddict import OrderedDict
import yaml


class OrderedDictYAMLLoader(yaml.SafeLoader):
    """Based on: https://gist.github.com/844388"""

    def __init__(self, *args, **kwargs):
        yaml.SafeLoader.__init__(self, *args, **kwargs)
        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                                                    'expected a mapping node, but found {}'.format(node.id),
                                                    node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                                                        node.start_mark, 'found unacceptable key ({})'.format(exc),
                                                        key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


class AttrDict(OrderedDict):
    """ https://github.com/mk-fg/layered-yaml-attrdict-config """

    def __init__(self, *argz, **kwz):
        super(AttrDict, self).__init__(*argz, **kwz)

    def __setitem__(self, k, v):
        super(AttrDict, self).__setitem__(k, AttrDict(v) if isinstance(v, Mapping) else v)

    def __getattr__(self, k):
        if not (k.startswith('__') or k.startswith('_OrderedDict__')):
            return self[k]
        else:
            return super(AttrDict, self).__getattr__(k)

    def __setattr__(self, k, v):
        if k.startswith('_OrderedDict__'):
            return super(AttrDict, self).__setattr__(k, v)
        self[k] = v

    @classmethod
    def from_yaml(cls, path, if_exists=False):
        if if_exists and not os.path.exists(path):
            return cls()
        return cls(yaml.load(open(path), OrderedDictYAMLLoader))

    def dump(self, stream=None):
        yaml.representer.SafeRepresenter.add_representer(
            AttrDict, yaml.representer.SafeRepresenter.represent_dict)
        yaml.representer.SafeRepresenter.add_representer(
            OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
        yaml.representer.SafeRepresenter.add_representer(
            defaultdict, yaml.representer.SafeRepresenter.represent_dict)
        yaml.representer.SafeRepresenter.add_representer(
            set, yaml.representer.SafeRepresenter.represent_list)
        return yaml.safe_dump(self, stream,
                              default_flow_style=False, encoding='utf-8')
