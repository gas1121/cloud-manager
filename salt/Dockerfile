FROM bbinet/salt-master

ARG VULTR_KEY
ARG DIGITALOCEAN_TOKEN
ARG USE_MIRROR=0

# use ustc mirror
RUN if [ $USE_MIRROR ]; then sed -i 's/httpredir.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; fi
RUN if [ $USE_MIRROR ]; then sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; fi

# add salt-cloud salt-minion
RUN apt-get update && apt-get install -yq --no-install-recommends \
  salt-cloud salt-minion
# install gettext for envsubst
RUN apt-get update && apt-get install -y gettext-base

# copy config files
COPY ./etc /etc

# use envsubst to generate profiles
WORKDIR /etc/salt/cloud.providers.d
RUN envsubst < vultr.conf.temp > vultr.conf
RUN envsubst < digitalocean.conf.temp > digitalocean.conf
WORKDIR /
