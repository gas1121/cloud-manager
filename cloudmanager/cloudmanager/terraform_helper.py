import os

import docker

from .util import get_secrets_path


class TerraformHelper(object):
    def __init__(self):
        self.client = docker.DockerClient(
            base_url='unix://var/run/docker.sock')

    def do_terraform_scale_job(self, master_count, servant_count):
        """
        scale cloud to required vps count
        """
        environment = {
            'TF_VAR_MASTER_COUNT': master_count,
            'TF_VAR_MASTER_PLAN': os.getenv('TF_VAR_MASTER_PLAN', 'starter'),
            'TF_VAR_SERVANT_COUNT': servant_count,
            'TF_VAR_SERVANT_PLAN': os.getenv('TF_VAR_SERVANT_PLAN', 'starter'),
        }
        # get secrets path
        secrets_path = get_secrets_path(self.client)
        volumes = {
            'tf-workspace': {'bind': '/app', 'mode': 'rw'},
            secrets_path: {'bind': '/var/run/secrets', 'mode': 'rw'},
        }
        # ensure project's terraform container image exist
        self.client.images.get('cloud-manager-terraform')
        self.client.containers.run(
            'cloud-manager-terraform', command="terraform init",
            environment=environment, volumes=volumes)
        self.client.containers.run(
            'cloud-manager-terraform', command="terraform apply",
            environment=environment, volumes=volumes)
        result = self.client.containers.run(
            'cloud-manager-terraform',
            environment=environment, volumes=volumes,
            command='bash -c "terraform output -json"')
        return result
