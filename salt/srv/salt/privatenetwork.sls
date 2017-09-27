{% if salt['pillar.get']('privatenetwork', None) %}
private-network:
  network.managed:
    - name: ens7
    - enabled: True
    - type: eth
    - proto: static
    - ipaddr: {{ salt['pillar.get']('privatenetwork:ip') }}
    - netmask: 255.255.0.0
    - mtu: 1450
{% endif %}
