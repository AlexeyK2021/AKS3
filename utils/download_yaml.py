import requests
import yaml


if __name__ == '__main__':
    response = requests.get("http://127.0.0.1:5052/api/openapi.json")
    data = response.json()

    with open("../read/download.yaml", "w") as f:
        yaml.dump(data, f, sort_keys=False)