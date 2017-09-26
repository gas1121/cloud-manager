import unittest
from unittest.mock import MagicMock, patch

from cloudmanager.util import get_secrets_path


class TestUtil(unittest.TestCase):
    @patch('cloudmanager.util.docker')
    def test_get_secrets_path(self, docker):
        apiclient = MagicMock()
        client = MagicMock()
        container = MagicMock()
        container.id = 1
        client.containers.list.return_value = [container]
        docker.APIClient.return_value = apiclient
        docker.DockerClient.return_value = client

        # client not passed and target not found
        apiclient.inspect_container.return_value = {
            'Mounts': [{
                'Destination': 'dest',
                'Source': 'testPath1',
            }]
        }
        result = get_secrets_path()
        docker.DockerClient.assert_called_once()
        docker.APIClient.assert_called_once()
        client.containers.list.assert_called_once()
        apiclient.inspect_container.assert_called_once_with(1)
        self.assertEqual(result, "")
        client.containers.list.reset_mock()
        docker.DockerClient.reset_mock()
        docker.APIClient.reset_mock()
        apiclient.inspect_container.reset_mock()

        # client passed with target found
        apiclient.inspect_container.return_value = {
            'Mounts': [{
                'Destination': 'secrets',
                'Source': 'testPath2',
            }]
        }
        result = get_secrets_path(client)
        docker.DockerClient.assert_not_called()
        docker.APIClient.assert_called_once()
        client.containers.list.assert_called_once()
        apiclient.inspect_container.assert_called_once_with(1)
        self.assertEqual(result, "testPath2")
