{% set compose_version=salt['pillar.get']('docker:compose:version', '1.16.2') %}

docker.install:
  cmd.run:
    - name: curl -fsSL get.docker.com -o get-docker.sh && sh get-docker.sh
    - unless: 
      - docker -v 2>/dev/null

{%- if salt['pillar.get']('docker:mirror:url', None) %}
docker.mirror:
  file.managed:
    - name: /etc/docker/daemon.json
    - source: salt://docker/daemon.json
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - defaults:
        url: https://docker.mirrors.ustc.edu.cn/
    - context:
        url: {{ salt['pillar.get']('docker:mirror:url', None) }}
{% endif %}

docker-compose.install:
  cmd.run:
    - names: 
      - curl -L https://github.com/docker/compose/releases/download/{{ compose_version }}/docker-compose-`uname -s`-`uname -m` > ~/docker-compose
      - sudo mv ~/docker-compose /usr/local/bin/docker-compose
      - sudo chmod +x /usr/local/bin/docker-compose
    - unless: 
      - docker-compose -v 2>/dev/null

docker.running:
  service.running:
    - name: docker
    - require:
      - docker.install
{%- if salt['pillar.get']('docker:mirror:url', None) %}
    - watch:
      - file: /etc/docker/daemon.json
{% endif %}
