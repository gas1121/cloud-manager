import unittest
from unittest.mock import MagicMock, patch

import arrow
from docker.errors import DockerException

from cloudmanager.cloud_manager import CloudManager
from cloudmanager.exceptions import (MasterCountChangeError,
                                     TerraformOperationError,
                                     ClusterSetupError)


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

    @patch('cloudmanager.cloud_manager.json.loads')
    @patch('cloudmanager.cloud_manager.SaltHelper')
    @patch('cloudmanager.cloud_manager.TerraformHelper')
    def test_check_cloud(self, TerraformHelper_mock, SaltHelper_mock,
                         load_mock):
        tf_helper_mock = TerraformHelper_mock()
        salt_helper_mock = SaltHelper_mock()

        # request not changed
        self.manager._get_max_scale_number = MagicMock(
            return_value=(0, 0, 0, arrow.now().format('YYYYMMDD HHmmss')))
        self.manager.check_cloud()
        tf_helper_mock.do_terraform_scale_job.assert_not_called()

        self.manager._get_max_scale_number = MagicMock(
            return_value=(3, 1, 2, arrow.now().format('YYYYMMDD HHmmss')))

        # terraform operation failed
        tf_helper_mock.do_terraform_scale_job = MagicMock(
            side_effect=DockerException)
        self.assertRaises(TerraformOperationError,
                          self.manager.check_cloud)
        tf_helper_mock.do_terraform_scale_job = MagicMock()

        # salt job failed
        salt_helper_mock.is_cluster_set_up.return_value = False
        self.assertRaises(ClusterSetupError,
                          self.manager.check_cloud)
        tf_helper_mock.do_terraform_scale_job.reset_mock()
        salt_helper_mock.do_salt_init_job.reset_mock()

        # success
        salt_helper_mock.is_cluster_set_up.return_value = True
        load_mock.return_value = {'test': 'value'}
        salt_helper_mock.prepare_salt_data = MagicMock()
        self.manager.check_cloud()
        tf_helper_mock.do_terraform_scale_job.assert_called_once_with(1, 2)
        salt_helper_mock.prepare_salt_data.assert_called_once_with(
            {'test': 'value'})
        salt_helper_mock.do_salt_init_job.assert_called_once_with()
        self.assertEqual(self.manager.curr_server_count, (1, 2))

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
        result = self.manager._get_max_scale_number()
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 0)
        self.assertEqual(result[2], 0)

        time_str = arrow.now().format('YYYYMMDD HHmmss')
        self.manager.scale_dict = {
            'key1': (2, 0, 2, time_str),
            'key2': (4, 0, 4, time_str),
            'key3': (3, 0, 3, time_str),
        }
        result = self.manager._get_max_scale_number()
        self.assertEqual(result, (4, 0, 4, time_str))
