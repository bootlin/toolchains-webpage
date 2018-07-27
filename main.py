#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Florent Jacquet <florent.jacquet@bootlin.com>
#

import sys
import os
import unicodedata
import re
import json

from collections import OrderedDict
from datetime import datetime

from jinja2 import FileSystemLoader, Environment

from toolchain import Toolchain, ToolchainEncoder, ToolchainSet

def to_json(value):
    return json.dumps(value, cls=ToolchainEncoder)

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
    start_time = datetime.now()
    toolchains = ToolchainSet()
    # Iterate over all releases
    for release in [e for e in os.scandir(TOOLCHAINS_DIR) if e.is_dir()]:
        toolchains_path = os.path.join(TOOLCHAINS_DIR, release.name)
        toolchain_list = []
        for a in os.scandir(os.path.join(toolchains_path, "toolchains")):
            try:
                toolchain_list += os.scandir(os.path.join(toolchains_path, "toolchains", a.name, 'available_toolchains'))
            except FileNotFoundError:
                pass
        # Iterate over all toolchains
        for toolchain in sorted([e for e in toolchain_list if e.is_file() and not e.name.startswith('.') and not e.name.endswith(".sha256")], key=lambda t: t.name):
            t = Toolchain(toolchain.name)

            with open(os.path.join(toolchains_path, "toolchains", t.arch,
                "readmes", t.name + ".txt")) as f:
                t.set_manifest(f)

            with open(os.path.join(toolchains_path, "toolchains", t.arch,
                "summaries", t.name + ".csv")) as f:
                t.set_summary(f)

            toolchains.add(release.name, t)

    for p in ['index', 'status', 'faq', 'news']:
        template = jinja_env.get_template("templates/%s.jinja" % p)
        html = template.render(
                toolchains=toolchains,
                datetime=datetime,
                start_time=start_time
                )
        with open(os.path.join(WWW_DIR, p + ".html"), 'w') as f:
            f.write(html)
        print("Page generated in", os.path.join(WWW_DIR, p + ".html"))

    main_release = "releases"
    template = jinja_env.get_template("templates/arch_listing.jinja")
    for a in toolchains.arch_list(main_release):
        page_name = "%s_%s" % (main_release, a)
        html = template.render(
                release=main_release,
                arch=a,
                toolchains=toolchains,
                datetime=datetime,
                start_time=start_time
                )
        with open(os.path.join(WWW_DIR, page_name + ".html"), 'w') as f:
            f.write(html)
        print("Page generated in", os.path.join(WWW_DIR, page_name + ".html"))

    template = jinja_env.get_template("templates/toolchains.jinja")
    page_name = "toolchains"
    html = template.render(
        release=main_release,
        toolchains=toolchains,
        datetime=datetime,
        start_time=start_time
        )
    with open(os.path.join(WWW_DIR, page_name + ".html"), 'w') as f:
        f.write(html)
    print("Page generated in", os.path.join(WWW_DIR, page_name + ".html"))


if __name__ == "__main__":
    generate()

