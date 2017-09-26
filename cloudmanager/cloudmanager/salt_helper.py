import json

import docker
from jinja2 import Environment, PackageLoader

from .util import get_secrets_path


class SaltHelper(object):
    def __init__(self):
        self.roster_file = "/cloud-manager-share/roster"
        self.client = docker.DockerClient(
            base_url='unix://var/run/docker.sock')

    def prepare_salt_data(self, data):
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

    def do_salt_init_job(self, pillar_dict):
        # TODO master node clean job in salt
        volumes = self._get_volumes_dict()
        self.client.containers.run(
            'cloud-manager-salt', command='salt-ssh -i "*" state.apply '
            'pillar=' + json.dumps(pillar_dict), volumes=volumes)

    def is_cluster_set_up(self, master_count, servant_count):
        """
        check if cluster is set up properly
        """
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
