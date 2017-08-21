FROM golang:latest

ARG USE_MIRROR=0

# mirror setting

# use ustc mirrors if needed
COPY docker/set_mirror.sh /tmp/
RUN chmod +x /tmp/set_mirror.sh
RUN /tmp/set_mirror.sh $USE_MIRROR

# install terraform
ENV TERRAFORM_VERSION=0.10.2
ENV TERRAFORM_SHA256SUM=6c1b5ce1a78bc7bb895055052d9074e519f51293770871acfe2dbd289e2f2aaa

RUN apt-get update && apt-get install -y zip
RUN curl https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip > terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN echo "${TERRAFORM_SHA256SUM}  terraform_${TERRAFORM_VERSION}_linux_amd64.zip" > terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    sha256sum -c terraform_${TERRAFORM_VERSION}_SHA256SUMS && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /bin && \
    rm -f terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# add vultr and digitalocean plugin
RUN go get -u github.com/squat/terraform-provider-vultr

#ENV VULTR_PROVIDER_VERSION 0.1.2
#ADD https://github.com/elricsfate/terraform-provider-vultr/releases/download/v${VULTR_PROVIDER_VERSION}/terraform_provider_vultr-v${VULTR_PROVIDER_VERSION}.tar.gz /temp/terraform_provider_vultr-v${VULTR_PROVIDER_VERSION}.tar.gz
#RUN tar -xf /temp/terraform_provider_vultr-v${VULTR_PROVIDER_VERSION}.tar.gz -C /usr/local/bin

COPY docker/terraform/.terraformrc /root/.terraformrc

ENTRYPOINT ["/bin/terraform"]