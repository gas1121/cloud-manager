import datetime

import arrow
import docker


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

    def scale_cloud(self, key, count):
        self.scale_dict[key] = (
            count, arrow.now().format('YYYYMMDD hhmmss'))
        self.check_cloud()

    def check_cloud(self):
        # clean expired data
        self.clean_expired_data()
        # get current max scale number
        count = self.get_max_scale_number()
        # use terraform to scale cloud
        self.do_terraform_scale_job(count)
        # read data from terraform result
        data = self.read_vps_data()
        # TODO error handling
        # generate salt roster file with data
        self.create_roster_file(data)
        # use salt to do initialization job if needed
        self.do_salt_init_job()

    def clean_expired_data(self):
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

    def get_max_scale_number(self):
        if not self.scale_dict:
            return 0
        return max(list(self.scale_dict.values()))[0]

    def do_terraform_scale_job(self, count):
        """
        scale cloud to required vps count
        """
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        environment = {
            'TF_VAR_MASTER_COUNT': 0,
            'TF_VAR_MASTER_PLAN': 'starter',
            'TF_VAR_SERVANT_COUNT': count,
            'TF_VAR_SERVANT_PLAN': 'starter',
        }
        volumes = {
            'tf-workspace': {'bind': '/app', 'mode': 'rw'},
            'cloud-manager-share': {
                'bind': '/cloud-manager-share', 'mode': 'rw'},
            './docker/terraform': {'bind': '/terraform', 'mode': 'rw'},
            './secrets': {'bind': '/var/run/secrets', 'mode': 'rw'},
        }
        result = client.containers.run(
            'terraform', environment=environment, volumes=volumes)

    def read_vps_data(self):
        pass

    def create_roster_file(self, data):
        pass

    def do_salt_init_job(self):
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        volumes = {
            'tf-workspace': {'bind': '/app', 'mode': 'rw'},
            'cloud-manager-share': {
                'bind': '/cloud-manager-share', 'mode': 'rw'},
            './docker/terraform': {'bind': '/terraform', 'mode': 'rw'},
            './secrets': {'bind': '/var/run/secrets', 'mode': 'rw'},
        }
        result = client.containers.run('salt', volumes=volumes)
