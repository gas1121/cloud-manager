import os
import datetime
import json

import arrow
import docker
from jinja2 import Environment, PackageLoader


class CloudManager(object):
    """
    Manager for cloud vps resource with following rules:
        1. Store all request vps count and use max of them to create
        2. All request expire after 24 hours, and if no request left,
           destroy all created vps
        3. Every request come with a unique key to identify, and when
           scale down request come value stored with key is modified
    """
    def __init__(self):
        self.scale_dict = {}
        self.expire_hour = 24
        self.terraform_result_file = "/cloud-manager-share/result.json"

    def scale_cloud(self, key, count):
        self.scale_dict[key] = (
            count, arrow.now().format('YYYYMMDD hhmmss'))
        self.check_cloud()

    def check_cloud(self):
        # clean expired data
        self._clean_expired_data()
        # get current max scale number
        count = self._get_max_scale_number()
        # use terraform to scale cloud
        try:
            self._do_terraform_scale_job(count)
        except Exception:
            # TODO exception type
            # if terraform job failed, return and wait for next call
            return
        # read data from terraform result
        data = json.load(self.terraform_result_file)
        # TODO error handling
        # generate salt roster file and prepare pillar dict
        pillar_dict = self._prepare_salt_data(data)
        # use salt to do initialization job if needed
        self._do_salt_init_job(pillar_dict)

    def _clean_expired_data(self):
        """
        clean data that is over expire_hour
        """
        curr_time = arrow.now()
        filtered_dict = {}
        for key in self.scale_dict:
            item_time = arrow.get(
                self.scale_dict[key][1], 'YYYYMMDD hhmmss')
            if curr_time - item_time > datetime.timedelta(
                    hours=self.expire_hour):
                pass
            filtered_dict[key] = self.scale_dict[key]
        self.scale_dict = filtered_dict

    def _get_max_scale_number(self):
        if not self.scale_dict:
            return 0
        return max(list(self.scale_dict.values()))[0]

    def _get_secrets_path(self, client):
        # get secrets path on host by docker inspect current container
        container = client.containers.list(
            filters={'name': 'cloud-manager'})[0]
        api = docker.APIClient(base_url='unix://var/run/docker.sock')
        container_info = api.inspect_container(container.id)
        for mount in container_info['Mounts']:
            if 'secrets' in mount['Destination']:
                return mount['Source']
        return ""

    def _do_terraform_scale_job(self, count):
        """
        scale cloud to required vps count
        """
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        environment = {
            'TF_VAR_MASTER_COUNT': 0,
            'TF_VAR_MASTER_PLAN': os.getenv('TF_VAR_MASTER_PLAN', 'starter'),
            'TF_VAR_SERVANT_COUNT': count,
            'TF_VAR_SERVANT_PLAN': os.getenv('TF_VAR_SERVANT_PLAN', 'starter'),
        }
        # get secrets path
        secrets_path = self._get_secrets_path(client)
        volumes = {
            'tf-workspace': {'bind': '/app', 'mode': 'rw'},
            'cloud-manager-share': {
                'bind': '/cloud-manager-share', 'mode': 'rw'},
            secrets_path: {'bind': '/var/run/secrets', 'mode': 'rw'},
        }
        client.containers.run(
            'terraform', command="terraform init", environment=environment,
            volumes=volumes)
        client.containers.run(
            'terraform', command="terraform apply", environment=environment,
            volumes=volumes)
        client.containers.run(
            'terraform', environment=environment, volumes=volumes,
            command="terraform output -json > " + self.terraform_result_file)

    def _prepare_salt_data(self, data):
        # prepare data
        render_data = {}
        # refresh /cloud-manager-share/roster
        env = Environment(
            loader=PackageLoader('cloudmanager', package_path='templates'),
        )
        template = env.get_template('roster.jinja')
        with open('/cloud-manager-share/roster', 'rw') as f:
            f.write(template.render(render_data))
        # prepare salt pillar dict
        pillar_dict = {}
        # TODO
        return pillar_dict

    def _do_salt_init_job(self, pillar_dict):
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        # get secrets path
        secrets_path = self._get_secrets_path(client)
        volumes = {
            'cloud-manager-share': {
                'bind': '/cloud-manager-share', 'mode': 'rw'},
            secrets_path: {'bind': '/var/run/secrets', 'mode': 'rw'},
        }
        client.containers.run(
            'salt', command='salt-ssh -i "*" state.apply '
            'pillar=' + json.dumps(pillar_dict), volumes=volumes)
