import docker


def get_secrets_path(client=None):
    """
    get secrets path on host by docker inspect current container
    """
    if not client:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    container = client.containers.list(filters={'name': 'cloud-manager'})[0]
    api = docker.APIClient(base_url='unix://var/run/docker.sock')
    container_info = api.inspect_container(container.id)
    for mount in container_info['Mounts']:
        if 'secrets' in mount['Destination']:
            return mount['Source']
    return ""
