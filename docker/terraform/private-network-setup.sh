if [[ $1 ]]; then
    cat >> ./interfaces <<EOF
auto ens7
iface ens7 inet static
    address $1
    netmask 255.255.0.0
    mtu 1450
EOF
    ifup ens7
fi