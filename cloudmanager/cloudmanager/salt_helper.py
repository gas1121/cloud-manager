import os

import docker
from jinja2 import Environment, PackageLoader

from .util import get_secrets_path


class SaltHelper(object):
    def __init__(self):
        self.roster_file = "/cloud-manager-share/roster"
        self.pillar_folder = "/cloud-manager-share/pillar/"
        self.client = docker.DockerClient(
            base_url='unix://var/run/docker.sock')

        self.env = Environment(
            loader=PackageLoader('cloudmanager', package_path='templates'),
        )

    def prepare_salt_data(self, data):
        # prepare roster file
        self._prepare_roster(data)
        # prepare pillar data
        self._prepare_pillar(data)

    def _prepare_roster(self, data):
        """
        refresh /cloud-manager-share/roster
        @param data dict parsed from terraform's output
        """
        if not os.path.exists(os.path.dirname(self.roster_file)):
            os.makedirs(os.path.dirname(self.roster_file))
        template = self.env.get_template('roster.jinja')
        with open(self.roster_file, 'w') as f:
            f.write(template.render(data))

    def _prepare_pillar(self, data):
        """
        prepare pillar data in /cloud-manager-share/pillar/
        @param data dict parsed from terraform's output
        """
        if not os.path.exists(os.path.dirname(self.pillar_folder)):
            os.makedirs(os.path.dirname(self.pillar_folder))
        # render top.sls
        template = self.env.get_template('pillar/top.sls.jinja')
        with open(self.pillar_folder + 'top.sls', 'w') as f:
            f.write(template.render(data))
        # render privatenetwork.sls for each server
        template = self.env.get_template('pillar/privatenetwork.sls.jinja')
        for prefix in ['master', 'servant']:
            for idx, val in enumerate(data[prefix + '_ip_addresses']['value']):
                file_name = 'privatenetwork-{0}-{1}.sls'.format(
                    prefix, idx + 1)
                private_ip = data[
                    prefix + '_private_ip_addresses']['value'][idx]
                with open(self.pillar_folder + file_name, 'w') as f:
                    f.write(template.render({'private_ip': private_ip}))

    def do_salt_init_job(self):
        volumes = self._get_volumes_dict()
        self.client.containers.run(
            'cloud-manager-salt', command='salt-ssh -i "*" state.apply',
            volumes=volumes)

    def is_cluster_set_up(self, master_count, servant_count):
        """
        check if cluster is set up properly
        """
        # if master node is local machine, clean outdated node manually
        if master_count == 0:
            self._clean_node()
        # if master count is 0, then local machine is manager
        if master_count == 0:
            # check if swarm is setup properly by node count
            if len(self.client.nodes.list()) == servant_count + 1:
                return True
            else:
                return False
        else:
            volumes = self._get_volumes_dict()
            result = self.client.containers.run(
                'cloud-manager-salt', command='salt-ssh -i master-1 cmd.run '
                '"docker node ls --format \"{{json .}}\"" ', volumes=volumes)
            if len(result.splitlines()) == master_count + servant_count:
                return True
            else:
                return False

    def _clean_node(self):
        api = docker.APIClient(base_url='unix://var/run/docker.sock')
        clean_node_list = []
        nodes = api.nodes()
        for node in nodes:
            if node['Status']['State'] == 'down':
                clean_node_list.append(node['ID'])
        for node_id in clean_node_list:
            api.remove_node(node_id)

    def _get_volumes_dict(self):
        # get secrets path
        secrets_path = get_secrets_path(self.client)
        # named volume follow docker compose's rule
        volumes = {
            'cloudmanager_cloud-manager-share': {
                'bind': '/cloud-manager-share', 'mode': 'rw'},
            secrets_path: {'bind': '/var/run/secrets', 'mode': 'rw'},
        }
        return volumes
