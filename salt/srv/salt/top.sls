base:
  '*':
    - privatenetwork
    - docker
  'master-*':
    - docker.swarm
  'servant-*':
    - docker.swarm