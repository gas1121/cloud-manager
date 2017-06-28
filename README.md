# cloud-manager
A personal cloud manager to handle private cloud infrastructure. Provide utilities to scale cloud across different cloud hosting platform with docker invironment prepared.

## install
follow instruction on docker compose's [official site](https://docs.docker.com/compose/env-file/) to create a **.env** file.
in**.env**:
+ VULTR_KEY for vultr's api key
+ DIGITALOCEAN_TOKEN for digitalocean's api token
+ USE_MIRROR for whether to add ustc mirror to image