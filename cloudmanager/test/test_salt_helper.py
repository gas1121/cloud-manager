import unittest
from unittest.mock import MagicMock, patch, call

import yaml

from cloudmanager.salt_helper import SaltHelper


class TestSaltHelper(unittest.TestCase):
    def setUp(self):
        self.client_mock = MagicMock()
        with patch('cloudmanager.salt_helper.docker') as docker_mock:
            docker_mock.DockerClient.return_value = self.client_mock
            self.salt_helper = SaltHelper()
        self.terraform_output = {
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

    def test_prepare_salt_data(self):
        self.salt_helper._prepare_roster = MagicMock()
        self.salt_helper._prepare_pillar = MagicMock()
        self.salt_helper.prepare_salt_data(self.terraform_output)
        self.salt_helper._prepare_roster.assert_called_once_with(
            self.terraform_output)
        self.salt_helper._prepare_roster.assert_called_once_with(
            self.terraform_output)

    def test_prepare_roster(self):
        self.salt_helper.roster_file = '/tmp/cloud_manager_test/roster'
        self.salt_helper._prepare_roster(self.terraform_output)
        with open(self.salt_helper.roster_file, 'r') as f:
            text = f.read()
            roster_dict = yaml.safe_load(text)
            self.assertEqual(roster_dict['master-1']['host'], '1.1.1.1')
            self.assertEqual(roster_dict['master-2']['host'], '1.1.1.2')
            self.assertEqual(roster_dict['servant-1']['host'], '2.1.1.1')
            self.assertEqual(roster_dict['servant-2']['host'], '2.1.1.2')

    def test_prepare_pillar(self):
        self.salt_helper.pillar_folder = '/tmp/cloud_manager_test/pillar/'
        self.salt_helper._prepare_pillar(self.terraform_output)
        top_file = self.salt_helper.pillar_folder + '/top.sls'
        with open(top_file, 'r') as f:
            text = f.read()
            top_dict = yaml.safe_load(text)
            self.assertEqual(top_dict['base']['master-1'],
                             ['privatenetwork-master-1'])
            self.assertEqual(top_dict['base']['master-2'],
                             ['privatenetwork-master-2'])
            self.assertEqual(top_dict['base']['servant-1'],
                             ['privatenetwork-servant-1'])
            self.assertEqual(top_dict['base']['servant-2'],
                             ['privatenetwork-servant-2'])
        for prefix in ['master', 'servant']:
            for i in [0, 1]:
                file_name = self.salt_helper.pillar_folder + \
                    'privatenetwork-{0}-{1}.sls'.format(prefix, i + 1)
                with open(file_name, 'r') as f:
                    text = f.read()
                    curr_dict = yaml.safe_load(text)
                    expect_ip = self.terraform_output[
                        prefix + '_private_ip_addresses']['value'][i]
                    self.assertEqual(
                        curr_dict['privatenetwork']['ip'], expect_ip)

    def test_do_salt_init_job(self):
        self.salt_helper._get_volumes_dict = MagicMock(return_value={'a': {}})
        self.salt_helper.do_salt_init_job()
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

    @patch('cloudmanager.salt_helper.docker')
    def test_clean_node(self, docker_mock):
        docker_mock.APIClient().nodes.return_value = [{
                'ID': '1',
                'Status': {
                    'State': 'ready'
                }
            }, {
                'ID': '2',
                'Status': {
                    'State': 'down'
                }
            }, {
                'ID': '3',
                'Status': {
                    'State': 'down'
                }
            }]
        self.salt_helper._clean_node()
        docker_mock.APIClient().remove_node.assert_has_calls(
            [call('2'), call('3')])

    @patch('cloudmanager.salt_helper.get_secrets_path')
    def test_get_volumes_dict(self, get_secrets_path_mock):
        get_secrets_path_mock.return_value = 'path'
        result = self.salt_helper._get_volumes_dict()
        self.assertEqual(result, {
            'cloudmanager_cloud-manager-share': {
                'bind': '/cloud-manager-share', 'mode': 'rw'},
            'path': {'bind': '/var/run/secrets', 'mode': 'rw'},
        })
