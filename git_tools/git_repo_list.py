import os
import re

url_regex = r'url = (.*)($|\b)'
path = '.'

for item in os.listdir(path):
    config_path = os.path.join(path, item, '.git/config')
    if not os.path.exists(config_path):
        continue

    with open(config_path) as f:
        data = f.read()

    url = re.search(r'url = (.*)($|\b)', data).group(1)

    print(url)

