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
import csv

from collections import OrderedDict
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

TOOLCHAINS_DIR = "/srv/gitlabci/www/downloads"
WWW_DIR = "/srv/gitlabci/www"

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
    toolchains_tree = OrderedDict()
    archs = {}
    libcs = {}
    versions = {}
    # Iterate over all releases
    for release in [e for e in os.scandir(TOOLCHAINS_DIR) if e.is_dir()]:
        toolchains_path = os.path.join(TOOLCHAINS_DIR, release.name)
        toolchains[release.name] = {}
        toolchains_tree[release.name] = OrderedDict()
        archs[release.name] = set()
        libcs[release.name] = set()
        versions[release.name] = set()
        # Iterate over all toolchains
        for toolchain in sorted([e for e in os.scandir(os.path.join(toolchains_path, "toolchains")) if e.is_file() and not e.name.startswith('.') and not e.name.endswith(".sha256")], key=lambda t: t.name):
            toolchain_name = toolchain.name.split(".tar.")[0]
            arch, libc, version = toolchain_name.split("--")
            version = version.split('-20')[0]
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
            with open(os.path.join(toolchains_path, "readmes", toolchain_name + ".txt")) as f:
                toolchain_infos['manifest'] = f.read()
            flag = re.search(r"FLAG: (\S*)", toolchain_infos['manifest'])
            toolchain_infos['flag'] = flag.group(1)
            toolchain_infos['manifest'] = '\n'.join(toolchain_infos['manifest'].split('\n')[2:-2])

            summary_list = ['gdb', 'gcc-final', 'linux', 'uclibc', 'musl', 'glibc', 'binutils']
            found_list = []
            toolchain_infos['summary'] = []
            with open(os.path.join(toolchains_path, "summaries", toolchain_name + ".csv")) as f:
                summary = csv.reader(f, delimiter=",", quotechar='"')
                for row in summary:
                    if any(e in row[0] for e in summary_list if e not in found_list):
                        row[0] = row[0].replace("gcc-final", "gcc")
                        toolchain_infos['summary'].append([row[0], row[1]])
                        found_list.append(row[0])
            toolchain_infos['summary'] = sorted(toolchain_infos['summary'], key=lambda e: e[0])

            # Build the two dicts: the raw list and the tree
            toolchains[release.name][toolchain_name] = toolchain_infos
            if arch not in toolchains_tree[release.name].keys():
                toolchains_tree[release.name][arch] = OrderedDict()
            if libc not in toolchains_tree[release.name][arch].keys():
                toolchains_tree[release.name][arch][libc] = OrderedDict()
            if version not in toolchains_tree[release.name][arch][libc].keys():
                toolchains_tree[release.name][arch][libc][version] = []

            toolchains_tree[release.name][arch][libc][version].append(toolchain_infos)

    for p in ['index', 'status']:
        template = jinja_env.get_template(p + ".jinja")
        html = template.render(
                toolchains=toolchains,
                toolchains_tree=toolchains_tree,
                archs=archs,
                libcs=libcs,
                versions=versions,
                datetime=datetime,
                start_time=start_time
                )
        with open(os.path.join(WWW_DIR, p + ".html"), 'w') as f:
            f.write(html)
        print("Page generated in", os.path.join(WWW_DIR, p + ".html"))

if __name__ == "__main__":
    generate()

