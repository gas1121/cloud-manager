variable "MASTER_COUNT" {}
variable "MASTER_PLAN" {}
variable "SERVANT_COUNT" {}
variable "SERVANT_PLAN" {}

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

data "vultr_plan" "master" {
  filter {
    name   = "price_per_month"
    values = ["${var.MASTER_PLAN == "starter" ? "5.00" : "10.00"}"]
  }

  filter {
    name   = "ram"
    values = ["${var.MASTER_PLAN == "starter" ? "1024" : "2048"}"]
  }
}

data "vultr_plan" "servant" {
  filter {
    name   = "price_per_month"
    values = ["${var.SERVANT_PLAN == "starter" ? "5.00" : "10.00"}"]
  }

  filter {
    name   = "ram"
    values = ["${var.SERVANT_PLAN == "starter" ? "1024" : "2048"}"]
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
    count = "${var.MASTER_COUNT}"
    name = "master"
    hostname = "master"
    region_id = "${data.vultr_region.tokyo.id}"
    plan_id = "${data.vultr_plan.master.id}"
    os_id = "${data.vultr_os.ubuntu.id}"
    ssh_key_ids = ["${vultr_ssh_key.key.id}"]
    tag = "master"
    private_networking = true
}

resource "vultr_instance" "servant" {
    count = "${var.SERVANT_COUNT}"
    name = "servant"
    hostname = "servant"
    region_id = "${data.vultr_region.tokyo.id}"
    plan_id = "${data.vultr_plan.servant.id}"
    os_id = "${data.vultr_os.ubuntu.id}"
    ssh_key_ids = ["${vultr_ssh_key.key.id}"]
    tag = "servant"
    private_networking = true
}

output master_count {
    value = "${var.MASTER_COUNT}"
}

output master_ip_addresses {
    value = "${concat(list(vultr_instance.master.*.ipv4_address))}"
}

output master_private_ip_addresses {
    value = "${concat(list(vultr_instance.master.*.ipv4_private_address))}"
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
