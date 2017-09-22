import unittest
from unittest.mock import MagicMock

import arrow

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
        time = arrow.get(self.manager.scale_dict["key"][-1], 'YYYYMMDD hhmmss')
        time_str = time.format('YYYYMMDD hhmm')
        self.assertEqual(curr_time.format('YYYYMMDD hhmm'), time_str)
        self.assertRaises(MasterCountChangeError, self.manager.scale_cloud,
                          "key2", 0, 3)

    def test_check_cloud(self):
        # TODO
        pass

    def test_is_master_count_equal(self):
        result = self.manager._is_master_count_equal(0)
        self.assertTrue(result)
        time_str = arrow.now().format('YYYYMMDD hhmmss')
        self.manager.scale_dict = {'key1': (2, 1, 1, time_str)}
        result = self.manager._is_master_count_equal(0)
        self.assertFalse(result)

    def test_clean_expired_data(self):
        self.manager.scale_dict = {
            'key1': (2, 1, 1, arrow.now().shift(
                hours=-25).format('YYYYMMDD hhmmss')),
            'key2': (2, 1, 1, arrow.now().shift(
                hours=-23, minutes=-50).format('YYYYMMDD hhmmss')),
            'key3': (2, 1, 1, arrow.now().shift(
                hours=-1).format('YYYYMMDD hhmmss')),
        }
        self.manager._clean_expired_data()
        self.assertEqual(len(self.manager.scale_dict), 2)

    def test_get_max_scale_number(self):
        time_str = arrow.now().format('YYYYMMDD hhmmss')
        self.manager.scale_dict = {
            'key1': (2, 0, 2, time_str),
            'key2': (4, 0, 4, time_str),
            'key3': (3, 0, 3, time_str),
        }
        result = self.manager._get_max_scale_number()
        self.assertEqual(result, (4, 0, 4, time_str))

    def test_do_terraform_scale_job(self):
        # TODO
        pass
