import unittest
from unittest.mock import MagicMock, patch

import arrow
import yaml

from cloudmanager.cloud_manager import CloudManager
from cloudmanager.exceptions import MasterCountChangeError


class TestCloudManager(unittest.TestCase):
    def setUp(self):
        self.manager = CloudManager()

    def test_new_key(self):
        key_set = set()
        for i in range(0, 10):
            key_set.add(self.manager.new_key())
        self.assertEqual(len(key_set), 10)

    def test_scale_cloud(self):
        self.manager.check_cloud = MagicMock()
        curr_time = arrow.now()
        self.manager.scale_cloud("key", 1, 2)
        self.assertTrue("key" in self.manager.scale_dict)
        self.assertEqual(self.manager.scale_dict["key"][0], 3)
        self.assertEqual(self.manager.scale_dict["key"][1], 1)
        self.assertEqual(self.manager.scale_dict["key"][2], 2)
        time = arrow.get(self.manager.scale_dict["key"][-1], 'YYYYMMDD HHmmss')
        time_str = time.format('YYYYMMDD HHmm')
        self.assertEqual(curr_time.format('YYYYMMDD HHmm'), time_str)
        self.assertRaises(MasterCountChangeError, self.manager.scale_cloud,
                          "key2", 0, 3)

    @patch('cloudmanager.cloud_manager.json.load')
    def test_check_cloud(self, load_mock):
        self.manager._clean_expired_data = MagicMock()
        self.manager._get_max_scale_number = MagicMock(
            return_value=(3, 1, 2, arrow.now().format('YYYYMMDD HHmmss')))
        self.manager._do_terraform_scale_job = MagicMock()
        load_mock.return_value = {'test': 'value'}
        self.manager._prepare_salt_data = MagicMock(return_value={})
        self.manager._do_salt_init_job = MagicMock()
        self.manager.check_cloud()
        self.manager._clean_expired_data.assert_called_once()
        self.manager._get_max_scale_number.assert_called_once()
        self.manager._do_terraform_scale_job.assert_called_once_with(1, 2)
        self.manager._prepare_salt_data.assert_called_once_with(
            {'test': 'value'})
        self.manager._do_salt_init_job.assert_called_once_with({})
        # TODO job with exceptions

    def test_is_master_count_equal(self):
        result = self.manager._is_master_count_equal(0)
        self.assertTrue(result)
        time_str = arrow.now().format('YYYYMMDD HHmmss')
        self.manager.scale_dict = {'key1': (2, 1, 1, time_str)}
        result = self.manager._is_master_count_equal(0)
        self.assertFalse(result)

    def test_clean_expired_data(self):
        self.manager.scale_dict = {
            'key1': (2, 1, 1, arrow.now().shift(
                hours=-25).format('YYYYMMDD HHmmss')),
            'key2': (2, 1, 1, arrow.now().shift(
                hours=-23, minutes=-50).format('YYYYMMDD HHmmss')),
            'key3': (2, 1, 1, arrow.now().shift(
                hours=-1).format('YYYYMMDD HHmmss')),
        }
        self.manager._clean_expired_data()
        self.assertEqual(len(self.manager.scale_dict), 2)

    def test_get_max_scale_number(self):
        time_str = arrow.now().format('YYYYMMDD HHmmss')
        self.manager.scale_dict = {
            'key1': (2, 0, 2, time_str),
            'key2': (4, 0, 4, time_str),
            'key3': (3, 0, 3, time_str),
        }
        result = self.manager._get_max_scale_number()
        self.assertEqual(result, (4, 0, 4, time_str))

    @patch('cloudmanager.cloud_manager.docker.DockerClient')
    def test_do_terraform_scale_job(self, dockerclient_mock):
        client = MagicMock()
        dockerclient_mock.return_value = client
        self.manager._get_secrets_path = MagicMock(return_value='path')
        self.manager._do_terraform_scale_job(1, 2)
        self.manager._get_secrets_path.assert_called_once_with(client)
        self.assertEqual(client.containers.run.call_count, 3)

    @patch('cloudmanager.cloud_manager.docker.APIClient')
    def test_get_secrets_path(self, apiclient_mock):
        client = MagicMock()
        container = MagicMock()
        container.id = 1
        client.containers.list.return_value = [container]
        apiclient_mock().inspect_container.return_value = {
            'Mounts': [{
                'Destination': 'dest',
                'Source': 'testPath1',
            }]
        }
        result = self.manager._get_secrets_path(client)
        client.containers.list.assert_called_once()
        apiclient_mock().inspect_container.assert_called_once_with(1)
        self.assertEqual(result, "")
        client.containers.list.reset_mock()
        apiclient_mock().inspect_container.reset_mock()

        apiclient_mock().inspect_container.return_value = {
            'Mounts': [{
                'Destination': 'secrets',
                'Source': 'testPath2',
            }]
        }
        result = self.manager._get_secrets_path(client)
        client.containers.list.assert_called_once()
        apiclient_mock().inspect_container.assert_called_once_with(1)
        self.assertEqual(result, "testPath2")

    def test_prepare_salt_data(self):
        self.manager.roster_file = '/tmp/roster_test'
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
        result = self.manager._prepare_salt_data(data)
        with open(self.manager.roster_file, 'r') as f:
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

    @patch('cloudmanager.cloud_manager.docker.DockerClient')
    def test_do_salt_init_job(self, dockerclient_mock):
        client = MagicMock()
        dockerclient_mock.return_value = client
        self.manager._get_secrets_path = MagicMock(return_value='path')
        pillar_dict = {'a': 'b'}
        self.manager._do_salt_init_job(pillar_dict)
        self.manager._get_secrets_path.assert_called_once_with(client)
        client.containers.run.assert_called_once()
