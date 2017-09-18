FROM python:latest

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install dependency
COPY cloudmanager /app
WORKDIR /app
RUN pip install -r requirements.txt
