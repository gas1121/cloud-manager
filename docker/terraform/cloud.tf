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

    provisioner "file" {
        source      = "ubuntu-init.sh"
        destination = "/tmp/ubuntu-init.sh"
        connection {
            host = "${self.ipv4_address}"
            type = "ssh"
            user = "root"
            password    = "${self.default_password}"
            private_key = "${file("/var/run/secrets/SSH_PRIVATE_KEY")}"
            timeout     = "2m"
        }
    }

    provisioner "remote-exec" {
        inline = [
            "ls /tmp/",
            "docker -v",
            "docker-compose -v",
            "ip -o addr",
            "chmod +x /tmp/ubuntu-init.sh",
            ". /tmp/ubuntu-init.sh"
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

resource "vultr_ipv4" "extra_ip" {
  instance_id = "${vultr_instance.master.id}"
  reboot      = false
  count       = 1
}

output ip_addresses {
    value = "${concat(vultr_ipv4.extra_ip.*.ipv4_address, list(vultr_instance.master.ipv4_address))}"
}

output initial_password {
    value = "${vultr_instance.master.default_password}"
}