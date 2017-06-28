FROM hashicorp/terraform

# add vultr plugin
ENV VULTR_PROVIDER_VERSION 0.1.2
ADD https://github.com/elricsfate/terraform-provider-vultr/releases/download/v${VULTR_PROVIDER_VERSION}/terraform_provider_vultr-v${VULTR_PROVIDER_VERSION}.tar.gz /temp/terraform_provider_vultr-v${VULTR_PROVIDER_VERSION}.tar.gz
RUN mkdir -p /opt/terraform-provider-vultr && tar -xf /temp/terraform_provider_vultr-v${VULTR_PROVIDER_VERSION}.tar.gz -C /opt/terraform-provider-vultr

COPY .terraformrc ~/.terraformrc
