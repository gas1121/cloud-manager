{% if salt['pillar.get']('network:private:address', None) %}
private-network:
  network.managed:
    - name: ens7
    - enabled: True
    - type: eth
    - proto: none
    - ipaddr: {{ pillar['network']['private']['address'] }}
    - netmask: 255.255.0.0
    - mtu: 1450
{% endif %}