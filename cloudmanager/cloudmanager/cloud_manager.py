import os
import datetime
import json

import arrow
import docker
from docker.errors import DockerException
from jinja2 import Environment, PackageLoader

from .exceptions import MasterCountChangeError, TerraformOperationFailError


class CloudManager(object):
    """
    Manage cloud vps resource with following rules:
        1. Store all request vps count and use max of them as vps number,
        2. All request expire after 24 hours, and if no request left,
           destroy all created vps
        3. Every request come with a unique key to identify
        4. Every 5 minutes cloud manager will check itself
        5. When scale is greater than 0, different master count is not allowed
    """
    def __init__(self):
        self.scale_dict = {}
        self.expire_hour = 24
        self.terraform_result_file = "/cloud-manager-share/result.json"
        self.roster_file = "/cloud-manager-share/roster"
        self.next_id = 0

    def new_key(self):
        """Generate new unique key
        """
        new_key = self.next_id
        self.next_id += 1
        return new_key

    def scale_cloud(self, key, master_count, servant_count):
        """
        @return master server ip
        """
        if not self._is_master_count_equal(master_count):
            raise MasterCountChangeError()
        total_count = master_count + servant_count
        self.scale_dict[key] = (total_count, master_count, servant_count,
                                arrow.now().format('YYYYMMDD HHmmss'))
        return self.check_cloud()

    def check_cloud(self):
        """
        @return master server ip
        """
        # clean expired data
        self._clean_expired_data()
        # get current max scale number
        _, master_count, servant_count, _ = self._get_max_scale_number()
        # use terraform to scale cloud
        try:
            self._do_terraform_scale_job(master_count, servant_count)
        except DockerException:
            # raise as terraform job failed
            raise TerraformOperationFailError()
        # read data from terraform result
        data = json.load(self.terraform_result_file)
        # TODO error handling
        # generate salt roster file and prepare pillar dict
        pillar_dict = self._prepare_salt_data(data)
        # use salt to do initialization job if needed
        self._do_salt_init_job(pillar_dict)

    def _is_master_count_equal(self, master_count):
        for key in self.scale_dict:
            if self.scale_dict[key][1] != master_count:
                return False
        return True

    def _clean_expired_data(self):
        """
        clean data that is over expire_hour
        """
        curr_time = arrow.now()
        filtered_dict = {}
        for key in self.scale_dict:
            item_time = arrow.get(
                self.scale_dict[key][-1], 'YYYYMMDD HHmmss')
            if curr_time - item_time > datetime.timedelta(
                    hours=self.expire_hour):
                continue
            filtered_dict[key] = self.scale_dict[key]
        self.scale_dict = filtered_dict

    def _get_max_scale_number(self):
        if not self.scale_dict:
            return 0
        return max(list(self.scale_dict.values()))

    def _do_terraform_scale_job(self, master_count, servant_count):
        """
        scale cloud to required vps count
        """
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        environment = {
            'TF_VAR_MASTER_COUNT': master_count,
            'TF_VAR_MASTER_PLAN': os.getenv('TF_VAR_MASTER_PLAN', 'starter'),
            'TF_VAR_SERVANT_COUNT': servant_count,
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
        # ensure project's terraform container image exist
        client.images.get('cloud-manager-terraform')
        # TODO volume issue
        client.containers.run(
            'cloud-manager-terraform', command="terraform init",
            environment=environment, volumes=volumes)
        client.containers.run(
            'cloud-manager-terraform', command="terraform apply",
            environment=environment, volumes=volumes)
        client.containers.run(
            'cloud-manager-terraform',
            environment=environment, volumes=volumes,
            command="terraform output -json > " + self.terraform_result_file)

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

    def _prepare_salt_data(self, data):
        # refresh /cloud-manager-share/roster
        env = Environment(
            loader=PackageLoader('cloudmanager', package_path='templates'),
        )
        template = env.get_template('roster.jinja')
        with open(self.roster_file, 'w') as f:
            f.write(template.render(data))
        # prepare salt pillar dict
        pillar_dict = {
            'master_privatenetwork': [],
            'servant_privatenetwork': [],
        }
        for index, value in enumerate(data['master_ip_addresses']['value']):
            pillar_dict['master_privatenetwork'].append({
                'ip': value,
                'private_ip': data[
                    'master_private_ip_addresses']['value'][index],
            })
        for index, value in enumerate(data['servant_ip_addresses']['value']):
            pillar_dict['servant_privatenetwork'].append({
                'ip': value,
                'private_ip': data[
                    'servant_private_ip_addresses']['value'][index],
            })
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
            'cloud-manager-salt', command='salt-ssh -i "*" state.apply '
            'pillar=' + json.dumps(pillar_dict), volumes=volumes)
