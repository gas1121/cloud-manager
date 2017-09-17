FROM python:latest

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# Upgrade System and Install dependencies 
RUN apt-get update && \
  apt-get upgrade -y -o DPkg::Options::=--force-confold && \
  apt-get install -y -o DPkg::Options::=--force-confold curl
# Install Latest Salt from the Develop Branch 
RUN curl -L https://bootstrap.saltstack.com | sh -s -- -X -L -M
# Install salt-ssh
RUN pip install salt-ssh


# Install salt-formulas
RUN mkdir -p /salt-formulas
WORKDIR /salt-formulas
#RUN git clone https://github.com/saltstack-formulas/apt-formula.git

COPY ./salt/master.d/master.conf /etc/salt/master.d/master.conf

WORKDIR /app

