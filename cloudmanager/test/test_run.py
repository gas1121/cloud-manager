import unittest
from unittest.mock import patch
import json

from run import app
from cloudmanager.exceptions import (MasterCountChangeError,
                                     TerraformOperationFailError)


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
        manager_mock.scale_cloud.return_value = "1.1.1.1"
        result = self.app.post('/scale')
        manager_mock.new_key.assert_called_once()
        manager_mock.scale_cloud.assert_called_once_with(
            "key", 0, 0)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'key')
        self.assertEqual(data['master_ip'], '1.1.1.1')
        manager_mock.reset_mock()

        # request with key exist
        manager_mock.scale_cloud.return_value = "2.1.1.1"
        result = self.app.post('/scale', data={
            'key': 'testkey', 'master_count': 1, 'servant_count': 2})
        manager_mock.new_key.assert_not_called()
        manager_mock.scale_cloud.assert_called_once_with(
            "testkey", 1, 2)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'testkey')
        self.assertEqual(data['master_ip'], '2.1.1.1')
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

        # request scheduled but failed this time
        manager_mock.scale_cloud.side_effect = \
            TerraformOperationFailError
        result = self.app.post('/scale', data={
            'key': 'testkey', 'master_count': 1, 'servant_count': 2})
        manager_mock.new_key.assert_not_called()
        manager_mock.scale_cloud.assert_called_once_with(
            "testkey", 1, 2)
        self.assertEqual(result.status_code, 500)
        data = json.loads(result.data)
        self.assertEqual(data['key'], 'testkey')
        self.assertEqual(
            data['message'], "Request is scheduled but failed this time, "
            "will retry later")
        manager_mock.reset_mock()

        # TODO unknown error
