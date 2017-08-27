variable "SERVANT_COUNT" {}

data "vultr_region" "tokyo" {
    filter {
        name = "name"
        values = ["Tokyo"]
    }
}

data "vultr_os" "ubuntu" {
    filter {
        name = "name"
        values = ["Ubuntu 16.04 x64"]
    }

    filter {
        name = "arch"
        values = ["x64"]
    }

    filter {
        name = "family"
        values = ["ubuntu"]
    }
}

data "vultr_plan" "starter" {
  filter {
    name   = "price_per_month"
    values = ["5.00"]
  }

  filter {
    name   = "ram"
    values = ["1024"]
  }
}

resource "vultr_ssh_key" "key" {
  name       = "key"
  public_key = "${file("/var/run/secrets/SSH_PUBLIC_KEY")}"
}

resource "vultr_firewall_group" "default" {
  description = "default group"
}

resource "vultr_firewall_rule" "ssh" {
  firewall_group_id = "${vultr_firewall_group.default.id}"
  cidr_block        = "0.0.0.0/0"
  protocol          = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "vultr_firewall_rule" "icmp" {
  firewall_group_id = "${vultr_firewall_group.default.id}"
  cidr_block        = "0.0.0.0/0"
  protocol          = "icmp"
}

resource "vultr_instance" "master" {
    name = "master"
    hostname = "master"
    region_id = "${data.vultr_region.tokyo.id}"
    plan_id = "${data.vultr_plan.starter.id}"
    os_id = "${data.vultr_os.ubuntu.id}"
    ssh_key_ids = ["${vultr_ssh_key.key.id}"]
    tag = "master"
    private_networking = true

    provisioner "remote-exec" {
        scripts = [
            "ubuntu-init.sh",
            "private-network-setup.sh ${self.ipv4_private_address}"
        ]
        connection {
            host = "${self.ipv4_address}"
            type = "ssh"
            user = "root"
            password    = "${self.default_password}"
            private_key = "${file("/var/run/secrets/SSH_PRIVATE_KEY")}"
            timeout     = "2m"
        }
    }
}

resource "vultr_instance" "servant" {
    count = "${var.SERVANT_COUNT}"
    name = "servant"
    hostname = "servant"
    region_id = "${data.vultr_region.tokyo.id}"
    plan_id = "${data.vultr_plan.starter.id}"
    os_id = "${data.vultr_os.ubuntu.id}"
    ssh_key_ids = ["${vultr_ssh_key.key.id}"]
    tag = "servant"
    private_networking = true

    provisioner "remote-exec" {
        scripts = [
            "ubuntu-init.sh",
            "private-network-setup.sh ${self.ipv4_private_address}"
        ]
        connection {
            host = "${self.ipv4_address}"
            type = "ssh"
            user = "root"
            password    = "${self.default_password}"
            private_key = "${file("/var/run/secrets/SSH_PRIVATE_KEY")}"
            timeout     = "2m"
        }
    }
}

output master_ip_addresses {
    value = "${concat(list(vultr_instance.master.ipv4_address))}"
}

output master_private_ip_addresses {
    value = "${concat(list(vultr_instance.master.ipv4_private_address))}"
}

output servant_count {
    value = "${var.SERVANT_COUNT}"
}

output servant_ip_addresses {
    value = "${concat(list(vultr_instance.servant.*.ipv4_address))}"
}

output servant_private_ip_addresses {
    value = "${concat(list(vultr_instance.servant.*.ipv4_private_address))}"
}
