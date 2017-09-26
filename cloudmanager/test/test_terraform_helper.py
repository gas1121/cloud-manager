import unittest
from unittest.mock import MagicMock, patch

from cloudmanager.terraform_helper import TerraformHelper


class TestTerraformHelper(unittest.TestCase):
    @patch('cloudmanager.terraform_helper.docker')
    @patch('cloudmanager.terraform_helper.get_secrets_path')
    def test_do_terraform_scale_job(self, get_secrets_path_mock, docker_mock):
        client = MagicMock()
        docker_mock.DockerClient.return_value = client

        tf_helper = TerraformHelper()
        client.containers.run.return_value = "result"
        get_secrets_path_mock.return_value = 'path'
        result = tf_helper.do_terraform_scale_job(1, 2)
        get_secrets_path_mock.assert_called_once_with(client)
        client.images.get.assert_called_once_with('cloud-manager-terraform')
        self.assertEqual(client.containers.run.call_count, 3)
        self.assertEqual(result, "result")
