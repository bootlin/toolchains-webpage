#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#

import sys
import os
import unicodedata
import re
import json

from datetime import datetime

from jinja2 import FileSystemLoader, Environment

def to_json(value):
    return json.dumps(value)

def slugify(value):
    """ Note: This was modified from django.utils.text slugify """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    return str(value)

jinja_env = Environment(loader=FileSystemLoader(os.getcwd()))
jinja_env.filters['slugify'] = slugify
jinja_env.filters['to_json'] = to_json
template = jinja_env.get_template("index.jinja")

TOOLCHAINS_DIR = "/home/skia/workspace/toolchains_webpage/www"

def generate():
    """
    toolchains = {
        "toolchain_name": <dict, toolchain_infos>
        }
    toolchains_tree = {
        "arch": {
            "libc": {
                "version": <dict, toolchain_infos>
                }
            }
        }
    """
    start_time = datetime.now()
    toolchains = {}
    toolchains_tree = {}
    archs = {}
    libcs = {}
    versions = {}
    # Iterate over all releases
    for release in [e for e in os.scandir(TOOLCHAINS_DIR) if e.is_dir()]:
        toolchains_path = os.path.join(TOOLCHAINS_DIR, release.name)
        toolchains[release.name] = {}
        toolchains_tree[release.name] = {}
        archs[release.name] = set()
        libcs[release.name] = set()
        versions[release.name] = set()
        # Iterate over all toolchains
        for toolchain in [e for e in os.scandir(os.path.join(toolchains_path, "toolchains")) if e.is_file()]:
            toolchain_name = toolchain.name.split(".tar.")[0]
            arch, libc, version = toolchain_name.split("--")
            version = version.split('-')[0]
            archs[release.name].add(arch)
            libcs[release.name].add(libc)
            versions[release.name].add(version)

            # Prepare the info dict
            toolchain_infos = {
                    'arch': arch,
                    'libc': libc,
                    'version': version,
                    'name': toolchain_name,
                    }
            with open(os.path.join(toolchains_path, "manifests", toolchain_name + ".txt")) as f:
                toolchain_infos['manifest'] = f.read()
            flag = re.search(r"FLAG: (\S*)", toolchain_infos['manifest'])
            toolchain_infos['flag'] = flag.group(1)
            toolchain_infos['manifest'] = '\n'.join(toolchain_infos['manifest'].split('\n')[2:-2])

            # Build the two dicts: the raw list and the tree
            toolchains[release.name][toolchain_name] = toolchain_infos
            if arch not in toolchains_tree[release.name].keys():
                toolchains_tree[release.name][arch] = {}
            if libc not in toolchains_tree[release.name][arch].keys():
                toolchains_tree[release.name][arch][libc] = {}
            if version not in toolchains_tree[release.name][arch][libc].keys():
                toolchains_tree[release.name][arch][libc][version] = []

            toolchains_tree[release.name][arch][libc][version].append(toolchain_infos)

    html = template.render(
            toolchains=toolchains,
            toolchains_tree=toolchains_tree,
            archs=archs,
            libcs=libcs,
            versions=versions,
            datetime=datetime,
            start_time=start_time
            )
    with open(os.path.join(TOOLCHAINS_DIR, "index.html"), 'w') as f:
        f.write(html)
    print(html)
    return html

if __name__ == "__main__":
    generate()

