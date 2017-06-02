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
    devices = {
        "device_name": {
            "test_name": [
                {
                    "job_id": 4000,
                    "job_name": "bleh",
                    "result": "pass",
                    },
                {
                    "job_id": 4001,
                    "job_name": "bleh--2",
                    "result": "fail",
                    }
            ]
            }
        }
    """
    start_time = datetime.now()
    toolchains = {}
    toolchains_tree = {}
    archs = {}
    libcs = {}
    versions = {}
    for release in [e for e in os.scandir(TOOLCHAINS_DIR) if e.is_dir()]:
        toolchains[release.name] = {}
        toolchains_tree[release.name] = {}
        archs[release.name] = set()
        libcs[release.name] = set()
        versions[release.name] = set()
        for toolchain in [e for e in os.scandir(os.path.join(TOOLCHAINS_DIR, release.name, "toolchains")) if e.is_file()]:
            arch, libc, version = toolchain.name.split("--")
            version = version.split('-')[0]
            archs[release.name].add(arch)
            libcs[release.name].add(libc)
            versions[release.name].add(version)
            toolchain_infos = {
                    'arch': arch,
                    'libc': libc,
                    'version': version,
                    'name': toolchain.name,
                    }
            toolchains[release.name][toolchain.name] = toolchain_infos
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
    with open("index.html", 'w') as f:
        f.write(html)
    print(html)
    return html

if __name__ == "__main__":
    generate()

