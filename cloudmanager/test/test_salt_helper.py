import unittest
from unittest.mock import MagicMock, patch

import yaml

from cloudmanager.salt_helper import SaltHelper


class TestSaltHelper(unittest.TestCase):
    def setUp(self):
        self.client_mock = MagicMock()
        with patch('cloudmanager.salt_helper.docker') as docker_mock:
            docker_mock.DockerClient.return_value = self.client_mock
            self.salt_helper = SaltHelper()

    def test_prepare_salt_data(self):
        self.salt_helper.roster_file = '/tmp/roster_test'
        data = {
            'master_ip_addresses': {
                'value': ['1.1.1.1', '1.1.1.2'],
            },
            'master_private_ip_addresses': {
                'value': ['10.1.1.1', '10.1.1.2'],
            },
            'servant_ip_addresses': {
                'value': ['2.1.1.1', '2.1.1.2'],
            },
            'servant_private_ip_addresses': {
                'value': ['20.1.1.1', '20.1.1.2'],
            },
        }
        result = self.salt_helper.prepare_salt_data(data)
        with open(self.salt_helper.roster_file, 'r') as f:
            text = f.read()
            roster_dict = yaml.safe_load(text)
            self.assertTrue('master-1' in roster_dict)
            self.assertEqual(roster_dict['master-1']['host'], '1.1.1.1')
            self.assertTrue('master-2' in roster_dict)
            self.assertEqual(roster_dict['master-2']['host'], '1.1.1.2')
            self.assertTrue('servant-1' in roster_dict)
            self.assertEqual(roster_dict['servant-1']['host'], '2.1.1.1')
            self.assertTrue('servant-2' in roster_dict)
            self.assertEqual(roster_dict['servant-2']['host'], '2.1.1.2')
        self.assertEqual(result, {
            'master_privatenetwork': [
                {'ip': '1.1.1.1', 'private_ip': '10.1.1.1'},
                {'ip': '1.1.1.2', 'private_ip': '10.1.1.2'},
            ],
            'servant_privatenetwork': [
                {'ip': '2.1.1.1', 'private_ip': '20.1.1.1'},
                {'ip': '2.1.1.2', 'private_ip': '20.1.1.2'},
            ]
        })

    def test_do_salt_init_job(self):
        self.salt_helper._get_volumes_dict = MagicMock(return_value={'a': {}})
        pillar_dict = {'a': 'b'}
        self.salt_helper.do_salt_init_job(pillar_dict)
        self.salt_helper._get_volumes_dict.assert_called_once()
        self.client_mock.containers.run.assert_called_once()

    def test_is_cluster_set_up(self):
        # master count is 0
        self.client_mock.nodes.list.return_value = [1, 1, 1]
        self.assertFalse(self.salt_helper.is_cluster_set_up(0, 3))
        self.assertTrue(self.salt_helper.is_cluster_set_up(0, 2))

        # master count is 1
        self.salt_helper._get_volumes_dict = MagicMock(return_value={'a': {}})
        self.client_mock.containers.run.return_value = "1\n2\n3\n"
        self.assertFalse(self.salt_helper.is_cluster_set_up(1, 3))
        self.assertTrue(self.salt_helper.is_cluster_set_up(1, 2))

    @patch('cloudmanager.salt_helper.get_secrets_path')
    def test_get_volumes_dict(self, get_secrets_path_mock):
        get_secrets_path_mock.return_value = 'path'
        result = self.salt_helper._get_volumes_dict()
        self.assertEqual(result, {
            'cloudmanager_cloud-manager-share': {
                'bind': '/cloud-manager-share', 'mode': 'rw'},
            'path': {'bind': '/var/run/secrets', 'mode': 'rw'},
        })
