FROM python:latest

ARG USE_MIRROR=0

EXPOSE 5000

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install dependency
COPY cloudmanager/requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY cloudmanager /app

CMD python  run.py
