import subprocess
import re


def main():
    result = subprocess.check_output(
        ["docker", "node", "ls", "--format", "'{{json .}}'"])
    outdate_node_list = []
    # extract all Down nodes' ID and remove them from swarm
    for line in result.splitlines():
        if re.findall(r'^.*?(Down).*?', line):
            outdate_node_list.extend(re.findall(r'^.*?ID":"(.*?)",.*?', line))
    for node_id in outdate_node_list:
        subprocess.check_output(["docker", "node", "rm", node_id])


if __name__ == '__main__':
    main()
