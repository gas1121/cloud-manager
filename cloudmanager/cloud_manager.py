import digitalocean
import vultr


def read_secret(file_name=None):
    with open(file_name) as f:
        secret = f.readline()
    return secret


class CloudManager(object):
    def __init__(self):
        self.managers = {}
        vultr_key = read_secret("secrets/vultr.txt")
        self.managers["vultr"] = vultr.Vultr(vultr_key)
        digitalocean_token = read_secret("secrets/digitalocean.txt")
        self.managers["digitalocean"] = digitalocean.Manager(
            token=digitalocean_token)

    def list_machine(self, host=None):
        result = {}
        result["vultr"] = self.managers["vultr"].plans.list()
        digitalocean_sizes = self.managers["digitalocean"].get_all_sizes()
        result["digitalocean"] = []
        for size in digitalocean_sizes:
            result["digitalocean"].append(size.slug)
        return result
