# cloud-manager
A personal cloud manager to handle private cloud infrastructure. Support scale cloud up and down with docker swarm prepared. Currently support vultr.

## Setup
+ create **vultr.txt** in **secret** folder and put you vultr key in it
+ create **digitalocean.txt** in **secret** folder and put you  digitalocean token in it
+ put ssh private key in **secret** folder with name **ssh-private-key**
+ put ssh public key in **secret** folder with name **ssh-key.pub**

## Usage
### As a single project
Set **TF_VAR_MASTER_COUNT**,**TF_VAR_SERVANT_COUNT** in **.env** file and run **docker-compose up terraform**, it will set your cloud properly
### Work with other project that need swarm cluster
run **docker-compose up -d cloud-manager** to run the cloud manager, then
use network **cloudmanager_cloud-manager** as a external network in other project, then send request to rest api running on **cloud-manager:5000**, the cloud manager will scale the cloud as request

## Env variable
+ **TF_VAR_MASTER_COUNT**: master server number, should only be 0 or 1
+ **TF_VAR_SERVANT_COUNT**: server instance number as servant node in docker swarm 