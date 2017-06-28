FROM bbinet/salt-master

# use ustc mirror
RUN if $USE_MIRROR; then sed -i 's/httpredir.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; fi
RUN if $USE_MIRROR; then sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; fi

# add salt-cloud salt-minion
RUN apt-get update && apt-get install -yq --no-install-recommends \
  salt-cloud salt-minion