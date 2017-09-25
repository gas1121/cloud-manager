import unittest
from unittest.mock import patch
import json

from run import app
from cloudmanager.exceptions import MasterCountChangeError


class TestRun(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    @patch('run.manager')
    def test_cloud_scale_api(self, manager_mock):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 404)
        result = self.app.get('/scale')
        self.assertEqual(result.status_code, 405)

        # first request
        manager_mock.new_key.return_value = "key"
        result = self.app.post('/scale')
        manager_mock.new_key.assert_called_once()
        manager_mock.scale_cloud.assert_called_once_with(
            "key", 0, 0)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'key')
        manager_mock.reset_mock()

        # request with key exist
        result = self.app.post('/scale', data={
            'key': 'testkey', 'master_count': 1, 'servant_count': 2})
        manager_mock.new_key.assert_not_called()
        manager_mock.scale_cloud.assert_called_once_with(
            "testkey", 1, 2)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'testkey')
        manager_mock.reset_mock()

        # master server count in request is different with exist one
        manager_mock.scale_cloud.side_effect = MasterCountChangeError
        result = self.app.post('/scale', data={
            'key': 'testkey', 'master_count': 1, 'servant_count': 2})
        manager_mock.new_key.assert_not_called()
        manager_mock.scale_cloud.assert_called_once_with(
            "testkey", 1, 2)
        self.assertEqual(result.status_code, 500)
        data = json.loads(result.data)
        self.assertEqual(
            data['message'], "Master server count required is different from"
            " exist request and not accepted")
        manager_mock.reset_mock()
