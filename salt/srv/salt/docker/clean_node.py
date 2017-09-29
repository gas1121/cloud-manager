import subprocess
import json


def main():
    result = subprocess.check_output(
        ["docker", "node", "ls", "--format", "'{{json .}}'"])
    for line in result.splitlines():
        print(json.loads(line))


if __name__ == '__main__':
    main()
