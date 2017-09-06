FROM python:latest

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install docker-py
RUN pip install docker

# install dependency
#COPY requirements.txt /tmp/
#RUN pip install -r /tmp/requirements.txt
