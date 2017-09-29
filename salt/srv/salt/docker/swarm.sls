{% set role=salt['pillar.get']('docker:swarm:role', None) %}
{% set advertise_addr=salt['pillar.get']('docker:swarm:advertise_addr', None) %}
{% set token=salt['pillar.get']('docker:swarm:token', None) %}
{% set master_addr=salt['pillar.get']('docker:swarm:master_addr', None) %}

include:
  - docker

{% if role and role == 'master' %}
docker.swarm.init:
  cmd.run:
    - name: >
        docker swarm init
        {%- if advertise_addr is defined %} --advertise-addr {{ advertise_addr }}{%- endif %}
    - unless:
      - "test -e /var/lib/docker/swarm/state.json"
      - "docker node ls"
    - require:
      - docker.running
docker.swarm.node.clean:
  cmd.script:
    - source: salt://docker/clean_node.py
    - shell: /bin/bash
{% endif %}
{% if role and role == 'worker' %}
docker.swarm.join:
  cmd.run:
    - name: docker swarm join --token {{ token }} {{ master_addr }}
    - unless:
      - docker info --format "{{ '{{ .Swarm }}' }}" | grep -w active
    - require:
      - docker.running
{% endif %}
