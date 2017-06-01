#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#

import sys
import os
import unicodedata
import re

from datetime import datetime

from jinja2 import FileSystemLoader, Environment

def slugify(value):
    """ Note: This was modified from django.utils.text slugify """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    return str(value)

jinja_env = Environment(loader=FileSystemLoader(os.getcwd()))
jinja_env.filters['slugify'] = slugify
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
    toolchains_by_arch = {}
    toolchains_by_libc = {}
    toolchains_by_version = {}
    toolchains = {}
    for directory in [e for e in os.scandir(TOOLCHAINS_DIR) if e.is_dir()]:
        toolchains[directory.name] = {}
        toolchains_by_arch[directory.name] = {}
        toolchains_by_libc[directory.name] = {}
        toolchains_by_version[directory.name] = {}
        for toolchain in [e for e in os.scandir(os.path.join(TOOLCHAINS_DIR, directory.name, "toolchains")) if e.is_file()]:
            arch, libc, version = toolchain.name.split("--")
            toolchain_infos = {
                    'arch': arch,
                    'libc': libc,
                    'version': version,
                    'name': toolchain.name,
                    }
            toolchains[directory.name][toolchain.name] = toolchain_infos
            try: toolchains_by_arch[directory.name][arch].append(toolchain_infos)
            except: toolchains_by_arch[directory.name][arch] = [toolchain_infos]
            try: toolchains_by_libc[directory.name][libc].append(toolchain_infos)
            except: toolchains_by_libc[directory.name][libc] = [toolchain_infos]
            try: toolchains_by_version[directory.name][version].append(toolchain_infos)
            except: toolchains_by_version[directory.name][version] = [toolchain_infos]

    html = template.render(
            toolchains=toolchains,
            toolchains_by_arch=toolchains_by_arch,
            toolchains_by_libc=toolchains_by_libc,
            toolchains_by_version=toolchains_by_version,
            datetime=datetime,
            start_time=start_time
            )
    with open("index.html", 'w') as f:
        f.write(html)
    print(html)
    return html

if __name__ == "__main__":
    generate()

