import unittest
from unittest.mock import patch
import json

from run import app


class TestRun(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    @patch('run.cloud_manager')
    def test_cloud_scale_api(self, cloud_manager_mock):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 404)
        result = self.app.get('/scale')
        self.assertEqual(result.status_code, 405)

        cloud_manager_mock.new_key.return_value = "key"
        cloud_manager_mock.scale_cloud.return_value = "1.1.1.1"
        result = self.app.post('/scale')
        cloud_manager_mock.new_key.assert_called_once()
        cloud_manager_mock.scale_cloud.assert_called_once_with(
            "key", 0, 0)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'key')
        self.assertEqual(data['master_ip'], '1.1.1.1')
        cloud_manager_mock.reset_mock()

        cloud_manager_mock.scale_cloud.return_value = "2.1.1.1"
        result = self.app.post('/scale', data={
            'key': 'testkey', 'master_count': 1, 'servant_count': 2})
        cloud_manager_mock.new_key.assert_not_called()
        cloud_manager_mock.scale_cloud.assert_called_once_with(
            "testkey", 1, 2)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'testkey')
        self.assertEqual(data['master_ip'], '2.1.1.1')
        cloud_manager_mock.reset_mock()

        cloud_manager_mock.scale_cloud.return_value = "3.1.1.1"
        result = self.app.post('/scale', query_string={
            'key': 'testkey2', 'master_count': 0, 'servant_count': 2})
        cloud_manager_mock.new_key.assert_not_called()
        cloud_manager_mock.scale_cloud.assert_called_once_with(
            "testkey2", 0, 2)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'testkey2')
        self.assertEqual(data['master_ip'], '3.1.1.1')
        cloud_manager_mock.reset_mock()

    def tearDown(self):
        pass
