{% set role=salt['pillar.get']('docker:swarm:role', 'worker') %}

include:
  - docker

{% if salt['pillar.get']('docker:swarm:worker', None) %}
#docker.swarm.join:
#  cmd.run:
#    - name: docker swarm join --token {{ pillar['docker']['swarm']['worker']['join-token'] }} {{ pillar['docker']['swarm']['worker']['manager-ip'] }}
#    - unless:
#      - docker info --format "{{ '{{' }}.Swarm{{ '}}' }}" | grep -w active
#    - require:
#      - docker.running
{% endif %}
{% if role=='manager' %}
docker.swarm.manger:
  cmd.run:
    - name:
    - unless:
      - "test -e /var/lib/docker/swarm/state.json"
      - "docker node ls | grep -q '{{ network.hostname }}'"
    - require:
      - docker.running
{% endif %}
{% if role=='worker' %}
docker.swarm.worker:
  cmd.run:
    - name:
    - unless:
      - 
    - require:
      - docker.running
{% endif %}
