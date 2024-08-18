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

from toolchain import Toolchain, ToolchainEncoder, ToolchainSet, OBSOLETE_ARCHITECTURES

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
    main_release = "releases"
    toolchains_path = os.path.join(TOOLCHAINS_DIR, main_release)
    toolchain_list = []

    # Find all toolchains
    for a in os.scandir(os.path.join(toolchains_path, "toolchains")):
        try:
            toolchain_list += os.scandir(os.path.join(toolchains_path, "toolchains",
                                                      a.name, 'available_toolchains'))
        except FileNotFoundError:
            pass
    # Iterate over all toolchains
    for toolchain in sorted([e for e in toolchain_list if e.is_file() and not e.name.startswith('.') and not e.name.endswith(".sha256")], key=lambda t: t.name):
        t = Toolchain(toolchain.name)

        arch_path = os.path.join(toolchains_path, "toolchains", t.arch)

        t.set_test_result(arch_path, t.name)

        tarball_dir = os.path.join(toolchains_path, "toolchains", t.arch,
                                   "tarballs")
        if os.path.exists(os.path.join(tarball_dir, t.name + ".tar.xz")):
            tarball_name = t.name + ".tar.xz"
        else:
            tarball_name = t.name + ".tar.bz2"

        t.set_tarball_name(tarball_name)

        with open(os.path.join(toolchains_path, "toolchains", t.arch,
                               "summaries", t.name + ".csv")) as f:
            t.set_summary(f)

        toolchains.add(main_release, t)

    for p in ['index', 'status', 'faq', 'news']:
        template = jinja_env.get_template("templates/%s.jinja" % p)
        html = template.render(
                toolchains=toolchains,
                obsolete_archs=OBSOLETE_ARCHITECTURES,
                datetime=datetime,
                start_time=start_time
                )
        with open(os.path.join(WWW_DIR, p + ".html"), 'w') as f:
            f.write(html)
        print("Page generated in", os.path.join(WWW_DIR, p + ".html"))

    template = jinja_env.get_template("templates/arch_listing.jinja")
    for a in toolchains.arch_list(main_release):
        page_name = "%s_%s" % (main_release, a)
        html = template.render(
                release=main_release,
                arch=a,
                toolchains=toolchains,
                obsolete_archs=OBSOLETE_ARCHITECTURES,
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

