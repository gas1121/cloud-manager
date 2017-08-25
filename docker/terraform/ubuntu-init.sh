#! /bin/bash

# initialization for ssh
# Disable password authentication
#grep -q "ChallengeResponseAuthentication" /etc/ssh/sshd_config && sed -i "/^[^#]*ChallengeResponseAuthentication[[:space:]]yes.*/c\ChallengeResponseAuthentication no" /etc/ssh/sshd_config || echo "ChallengeResponseAuthentication no" >> /etc/ssh/sshd_config
#grep -q "^[^#]*PasswordAuthentication" /etc/ssh/sshd_config && sed -i "/^[^#]*PasswordAuthentication[[:space:]]yes/c\PasswordAuthentication no" /etc/ssh/sshd_config || echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
#service ssh restart

# initialization for ubuntu mirror
# if needed, config ubuntu ustc mirror
if [[ "$1" == "use_mirror" ]]; then
    if cat /etc/apt/sources.list | grep "mirrors.ustc.edu.cn"; then
        echo "ustc mirror already setted, skip."
    else
        echo "set ustc mirror for ubuntu..."
        sed -i 's/archive.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
        apt-get update
    fi
fi

# initialization for docker
# install docker
if type docker 2>/dev/null; then
    echo "docker is installed, skip."
else
    echo "install docker..."
    apt-get update
    apt-get install -y curl linux-image-extra-$(uname -r) linux-image-extra-virtual
    apt-get install -y apt-transport-https ca-certificates
    curl -fsSL https://yum.dockerproject.org/gpg | sudo apt-key add -
    apt-key fingerprint 58118E89F3A912897C070ADBF76221572C52609D
    apt-get install -y software-properties-common
    add-apt-repository "deb https://apt.dockerproject.org/repo/ \
    ubuntu-$(lsb_release -cs) main"
    apt-get update
    apt-get -y install docker-engine
fi

# install docker compose
if type docker-compose 2>/dev/null; then
    echo "docker-compose is installed, skip."
else
    echo "install docker compose..."
    COMPOSE_VERSION=1.14.0
    COMPOSE_ADDRESS=https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-`uname -s`-`uname -m`
    if curl -L ${COMPOSE_ADDRESS} > /usr/local/bin/docker-compose; then
        chmod +x /usr/local/bin/docker-compose
    else
        echo "download docker compose failed."
        rm /usr/local/bin/docker-compose
    fi
fi

# if needed, config docker ustc mirror
if [[ "$1" == "use_mirror" ]] && [[ ! -f /etc/docker/daemon.json ]]; then
    echo "set ustc mirror for docker..."
    cat > /etc/docker/daemon.json <<EOF
{
    "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn/"]
}
EOF
    service docker restart
fi

# initialization for Python
# install python if needed
if ! type python 2>/dev/null; then
    echo "python not exist, install first..."
    apt-get install -y python
fi
# if needed, config pip ustc mirror
if [[ "$1" == "use_mirror" ]] && [[ ! -f ~/.pip/pip.conf ]]; then
    echo "set ustc mirror for pip..."
    if [[ ! -f ~/.pip ]]; then
        mkdir ~/.pip
    fi
    cat > ~/.pip/pip.conf <<EOF
[global]
index-url = https://mirrors.ustc.edu.cn/pypi/web/simple
format = columns
EOF
fi
# update pip and install virtualenv
if ! type pip 2>/dev/null; then
    echo "pip not exist, install first..."
    curl -L https://bootstrap.pypa.io/get-pip.py > get-pip.py
    python get-pip.py
fi
pip install -U pip
if pip list 2>/dev/null | grep "virtualenv" >/dev/null; then
    echo "virtualenv is installed, skip."
else
    pip install virtualenv
fi

# initialization for salt
# install salt

# initialization for port
# config port