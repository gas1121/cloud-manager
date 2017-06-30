FROM python:latest

ARG USE_MIRROR=0

# use ustc mirror if needed
RUN if [ $USE_MIRROR ]; then sed -i 's/httpredir.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; fi
RUN if [ $USE_MIRROR ]; then sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; fi
COPY pip.conf /tmp/
COPY set_pip_mirror.sh /tmp/
RUN /tmp/set_pip_mirror.sh
