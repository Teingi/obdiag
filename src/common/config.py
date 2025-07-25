#!/usr/bin/env python
# -*- coding: UTF-8 -*
# Copyright (c) 2022 OceanBase
# OceanBase Diagnostic Tool is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""
@file: config.py
@desc:
"""

from __future__ import absolute_import, division, print_function
import os
from src.common.file_crypto.file_crypto import FileEncryptor
from src.common.tool import ConfigOptionsParserUtil, DirectoryUtil
from src.common.stdio import SafeStdio
import oyaml as yaml
import pathlib
import sys
from collections import defaultdict


if getattr(sys, 'frozen', False):
    absPath = os.path.dirname(os.path.abspath(sys.executable))
else:
    absPath = os.path.dirname(os.path.abspath(__file__))
inner_config_release_path = os.path.join(absPath, "conf/inner_config.yml")
inner_config_dev_path = os.path.join(absPath, "../../conf/inner_config.yml")
if os.path.exists(inner_config_release_path):
    INNER_CONFIG_FILE = inner_config_release_path
else:
    INNER_CONFIG_FILE = inner_config_dev_path

DEFAULT_CONFIG_DATA = '''
obcluster:
  ob_cluster_name: obcluster
  db_host: 127.0.0.1
  db_port: 2881
  tenant_sys:
    user: root@sys
    password: ""
  servers:
    nodes:
      - ip: 127.0.0.1
    global:
      ssh_username: ''
      ssh_password: ''
      home_path: /root/observer
obproxy:
  obproxy_cluster_name: obproxy
  servers:
    nodes:
      - ip: 127.0.0.1
    global:
      ssh_username: ''
      ssh_password: ''
      home_path: /root/obproxy
'''

DEFAULT_INNER_CONFIG = {
    'obdiag': {
        'basic': {
            'config_path': '~/.obdiag/config.yml',
            'config_backup_dir': '~/.obdiag/backup_conf',
            'file_number_limit': 20,
            'file_size_limit': '2G',
            'dis_rsa_algorithms': 0,
            'strict_host_key_checking': 0,
        },
        'logger': {
            'log_dir': '~/.obdiag/log',
            'log_filename': 'obdiag.log',
            'file_handler_log_level': 'DEBUG',
            'log_level': 'INFO',
            'mode': 'obdiag',
            'stdout_handler_log_level': 'INFO',
            'error_stream': 'sys.stdout',
            'silent': False,
        },
        'ssh_client': {
            'remote_client_sudo': False,
        },
    },
    'analyze': {"thread_nums": 3},
    'check': {
        'ignore_version': False,
        'work_path': '~/.obdiag/check',
        'report': {
            'report_path': './check_report/',
            'export_type': 'table',
        },
        'package_file': '~/.obdiag/check/check_package.yaml',
        'tasks_base_path': '~/.obdiag/check/tasks/',
    },
    'gather': {'scenes_base_path': '~/.obdiag/gather/tasks', 'redact_processing_num': 3, "thread_nums": 3},
    'rca': {
        'result_path': './obdiag_rca/',
    },
}


class Manager(SafeStdio):

    RELATIVE_PATH = ''

    def __init__(self, home_path, stdio=None):
        self.stdio = stdio
        self.path = home_path
        self.is_init = self._mkdir(self.path)

    def _mkdir(self, path):
        return DirectoryUtil.mkdir(path, stdio=self.stdio)

    def _rm(self, path):
        return DirectoryUtil.rm(path, self.stdio)

    def load_config(self):
        try:
            with open(self.path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            self.stdio.exception(f"Configuration file '{self.path}' not found.")
        except yaml.YAMLError as exc:
            self.stdio.exception(f"Error parsing YAML file: {exc}")

    def load_config_with_defaults(self, defaults_dict):
        default_config = defaultdict(lambda: None, defaults_dict)
        try:
            with open(self.path, 'r') as stream:
                loaded_config = yaml.safe_load(stream)
        except FileNotFoundError:
            self.stdio.exception(f"Configuration file '{self.path}' not found.")
            return default_config
        except yaml.YAMLError as exc:
            self.stdio.exception(f"Error parsing YAML file: {exc}")
            return default_config
        combined_config = defaultdict(lambda: None, loaded_config)
        for section, values in default_config.items():
            if isinstance(values, dict):
                for key, default_value in values.items():
                    if section not in combined_config or key not in combined_config[section]:
                        combined_config[section][key] = default_value
            else:
                if section not in combined_config:
                    combined_config[section] = values
        return dict(combined_config)


class ConfigManager(Manager):

    def __init__(self, config_file=None, stdio=None, config_env_list=[], config_password=None):
        default_config_path = os.path.join(os.path.expanduser("~"), ".obdiag", "config.yml")
        if config_env_list is None or len(config_env_list) == 0:
            if config_file is None or not os.path.exists(config_file):
                config_file = default_config_path
                pathlib.Path(os.path.dirname(default_config_path)).mkdir(parents=True, exist_ok=True)
                with open(default_config_path, 'w') as f:
                    f.write(DEFAULT_CONFIG_DATA)

            super(ConfigManager, self).__init__(config_file, stdio)
            self.config_file = config_file
            if not self.config_file.endswith('.encrypted'):
                self.config_data = self.load_config()
            else:
                if config_password is None:
                    raise ValueError("config_password must be provided when decrypting a file")
                fileEncryptor = FileEncryptor(context=None, stdio=self.stdio)
                self.config_data = yaml.safe_load(fileEncryptor.decrypt_file(self.path, password=config_password))

        else:
            parser = ConfigOptionsParserUtil()
            self.config_data = parser.parse_config(config_env_list)

    def update_config_data(self, new_config_data, save_to_file=False):
        if not isinstance(new_config_data, dict):
            raise ValueError("new_config_data must be a dictionary")
        self.config_data.update(new_config_data)
        if save_to_file:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False)

    def _safe_get(self, dictionary, *keys, default=None):
        """Safe way to retrieve nested values from dictionaries"""
        current = dictionary
        for key in keys:
            try:
                current = current[key]
            except KeyError:
                return default
        return current

    @property
    def get_ocp_config(self):
        ocp = self._safe_get(self.config_data, 'ocp', 'login', default={})
        return {
            'url': ocp.get('url'),
            'user': ocp.get('user'),
            'password': ocp.get('password'),
        }

    @property
    def get_ob_cluster_config(self):
        ob_cluster = self.config_data.get('obcluster', {})
        nodes = ob_cluster.get('servers', {}).get('nodes', [])

        def create_ob_cluster_node(node_config, global_config):
            return {
                'ip': node_config.get('ip'),
                'ssh_username': node_config.get('ssh_username', global_config.get('ssh_username')),
                'ssh_password': node_config.get('ssh_password', global_config.get('ssh_password')),
                'ssh_port': node_config.get('ssh_port', global_config.get('ssh_port', 22)),
                'home_path': node_config.get('home_path', global_config.get('home_path', '/root/observer')),
                'data_dir': node_config.get('data_dir', global_config.get('data_dir', '/root/observer/store')),
                'redo_dir': node_config.get('redo_dir', global_config.get('redo_dir', '/root/observer/store')),
                'ssh_key_file': node_config.get('ssh_key_file', global_config.get('ssh_key_file', '')),
                'ssh_type': node_config.get('ssh_type', global_config.get('ssh_type', 'remote')),
                'container_name': node_config.get('container_name', global_config.get('container_name', '')),
                'namespace': node_config.get('namespace', global_config.get('namespace', '')),
                'pod_name': node_config.get('pod_name', global_config.get('pod_name', '')),
                "kubernetes_config_file": node_config.get('kubernetes_config_file', global_config.get('kubernetes_config_file', '')),
                'host_type': 'OBSERVER',
            }

        global_config = ob_cluster.get('servers', {}).get('global', {})
        ob_cluster_nodes = [create_ob_cluster_node(node, global_config) for node in nodes]

        return {
            'ob_cluster_name': ob_cluster.get('ob_cluster_name'),
            'db_host': ob_cluster.get('db_host'),
            'db_port': ob_cluster.get('db_port'),
            'tenant_sys': {
                'user': ob_cluster.get('tenant_sys', {}).get('user'),
                'password': ob_cluster.get('tenant_sys', {}).get('password'),
            },
            'servers': ob_cluster_nodes,
        }

    @property
    def get_obproxy_config(self):
        ob_proxy = self.config_data.get('obproxy', {})
        nodes = ob_proxy.get('servers', {}).get('nodes', [])

        def create_ob_proxy_node(node_config, global_config):
            return {
                'ip': node_config.get('ip'),
                'ssh_username': node_config.get('ssh_username', global_config.get('ssh_username', '')),
                'ssh_password': node_config.get('ssh_password', global_config.get('ssh_password', '')),
                'ssh_port': node_config.get('ssh_port', global_config.get('ssh_port', 22)),
                'home_path': node_config.get('home_path', global_config.get('home_path', '/root/obproxy')),
                'ssh_key_file': node_config.get('ssh_key_file', global_config.get('ssh_key_file', '')),
                'ssh_type': node_config.get('ssh_type', global_config.get('ssh_type', 'remote')),
                'container_name': node_config.get('container_name', global_config.get('container_name')),
                'namespace': node_config.get('namespace', global_config.get('namespace', '')),
                'pod_name': node_config.get('pod_name', global_config.get('pod_name', '')),
                "kubernetes_config_file": node_config.get('kubernetes_config_file', global_config.get('kubernetes_config_file', '')),
                'host_type': 'OBPROXY',
            }

        global_config = ob_proxy.get('servers', {}).get('global', {})
        ob_proxy_nodes = [create_ob_proxy_node(node, global_config) for node in nodes]

        return {
            'obproxy_cluster_name': ob_proxy.get('obproxy_cluster_name'),
            'servers': ob_proxy_nodes,
        }

    @property
    def get_oms_config(self):
        oms = self.config_data.get('oms', {})
        nodes = oms.get('servers', {}).get('nodes', [])

        def create_oms_node(node_config, global_config):
            return {
                'ip': node_config.get('ip'),
                'ssh_username': node_config.get('ssh_username', global_config.get('ssh_username', '')),
                'ssh_password': node_config.get('ssh_password', global_config.get('ssh_password', '')),
                'ssh_port': node_config.get('ssh_port', global_config.get('ssh_port', 22)),
                'home_path': node_config.get('home_path', global_config.get('home_path', '/root/obproxy')),
                'log_path': node_config.get('log_path', global_config.get('log_path', '/home/admin/logs')),
                'run_path': node_config.get('run_path', global_config.get('run_path', '/home/admin/run')),
                'store_path': node_config.get('store_path', global_config.get('store_path', '/home/admin/store')),
                'ssh_key_file': node_config.get('ssh_key_file', global_config.get('ssh_key_file', '')),
                'ssh_type': node_config.get('ssh_type', global_config.get('ssh_type', 'remote')),
                'container_name': node_config.get('container_name', global_config.get('container_name')),
                'namespace': node_config.get('namespace', global_config.get('namespace', '')),
                'pod_name': node_config.get('pod_name', global_config.get('pod_name', '')),
                "kubernetes_config_file": node_config.get('kubernetes_config_file', global_config.get('kubernetes_config_file', '')),
                'host_type': 'OMS',
            }

        global_config = oms.get('servers', {}).get('global', {})
        oms_nodes = [create_oms_node(node, global_config) for node in nodes]

        return {
            'oms_cluster_name': oms.get('oms_cluster_name'),
            'servers': oms_nodes,
        }

    def get_node_config(self, type, node_ip, config_item):
        nodes = []
        if type == 'ob_cluster':
            nodes = self.get_ob_cluster_config['servers']
        elif type == 'ob_proxy':
            nodes = self.get_obproxy_config['servers']
        else:
            self.stdio.exception(f"Unsupported cluster type: {type}")
        for node in nodes:
            if node['ip'] == node_ip:
                return node.get(config_item)
        return None


class InnerConfigManager(Manager):

    def __init__(self, stdio=None, inner_config_change_map=None):
        if inner_config_change_map is None:
            inner_config_change_map = {}
        inner_config_abs_path = os.path.abspath(INNER_CONFIG_FILE)
        super().__init__(inner_config_abs_path, stdio=stdio)
        self.config = self.load_config_with_defaults(DEFAULT_INNER_CONFIG)
        if inner_config_change_map != {}:
            self.config = self._change_inner_config(self.config, inner_config_change_map)

    def _change_inner_config(self, conf_map, change_conf_map):
        for key, value in change_conf_map.items():
            if key in conf_map:
                if isinstance(value, dict):
                    self._change_inner_config(conf_map[key], value)
                else:
                    conf_map[key] = value
            else:
                conf_map[key] = value
        return conf_map
