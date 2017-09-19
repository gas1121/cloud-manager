{% set minion_ip = grains['ip_interfaces:eth0:0'] %}
{% if salt['pillar.get']('privatenetwork', None) %}
{% for vps in salt['pillar.get']('privatenetwork') %}
{% if vps.ip == minion_ip %}
private-network:
  network.managed:
    - name: ens7
    - enabled: True
    - type: eth
    - proto: static
    - ipaddr: {{ vps.private_ip }}
    - netmask: 255.255.0.0
    - mtu: 1450
{% endif %}
{% endfor  %}
{% endif %}