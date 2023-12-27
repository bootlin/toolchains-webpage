import json
import csv
import re
import os

from collections import OrderedDict

OBSOLETE_ARCHITECTURES = ["sparcv8"]

class Toolchain(object):
    def __init__(self, file_name):
        toolchain_name = file_name.split(".tar.")[0]
        arch, libc, version = toolchain_name.split("--")
        version = version.split('-20')[0]
        self.arch = arch
        self.libc = libc
        self.version = version
        self.name = toolchain_name

    def set_test_result(self, arch_path, toolchain_name):
        # Newer toolchains have a <toolchain-name>-test-result.txt
        result_txt = os.path.join(arch_path, "test_results",
                                  toolchain_name + "-test-result.txt")
        if os.path.exists(result_txt):
            with open(result_txt) as f:
                self.test_result = f.read().strip()
        # Older toolchains have the test result direclty in the
        # readme.txt file
        else:
            readme_txt = os.path.join(arch_path, "readmes",
                                      toolchain_name + ".txt")
            with open(readme_txt) as f:
                readme = f.read()
                test_result = re.search(r"FLAG: (\S*)", readme)
                self.test_result = test_result.group(1)

    def set_summary(self, f):
        summary_list = ['gdb', 'gcc', 'linux', 'uclibc', 'musl', 'glibc', 'binutils']
        found_list = []
        summary = []
        s = csv.reader(f, delimiter=",", quotechar='"')
        for row in s:
            row[0] = row[0].replace("gcc-final", "gcc")
            if any(e in row[0] for e in summary_list if e not in found_list):
                summary.append([row[0], row[1]])
                found_list.append(row[0])
        self.summary = sorted(summary, key=lambda e: e[0])

    def get_binutils_version(self):
        for e in self.summary:
            if e[0] == 'binutils':
                return e[1]

    def get_libc_version(self):
        for e in self.summary:
            if e[0] == self.libc:
                return e[1]

    def get_linux_version(self):
        for e in self.summary:
            if e[0] == 'linux-headers':
                return e[1]

    def get_gdb_version(self):
        for e in self.summary:
            if e[0] == 'gdb':
                return e[1]

    def get_gcc_version(self):
        for e in self.summary:
            if e[0] == 'gcc':
                return e[1]

    def as_dict(self):
        return {
                'name': self.name,
                'arch': self.arch,
                'libc': self.libc,
                'version': self.version,
                'test_result': self.test_result,
                'summary': self.summary,
                }

class ToolchainEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Toolchain):
            return obj.as_dict()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

class ToolchainSet(object):
    def __init__(self):
        self.archs = {}
        self.libcs = {}
        self.versions = {}
        self.tree = OrderedDict()
        self.list_by_release = {}

    def add(self, release, t):
        if release not in self.list_by_release:
            self.list_by_release[release] = {}

        if release not in self.tree:
            self.tree[release] = OrderedDict()

        if release not in self.archs:
            self.archs[release] = set()

        if release not in self.libcs:
            self.libcs[release] = set()

        if release not in self.versions:
            self.versions[release] = set()

        self.archs[release].add(t.arch)
        self.libcs[release].add(t.libc)
        self.versions[release].add(t.version)

        if t.arch not in self.tree[release]:
            self.tree[release][t.arch] = OrderedDict()
        if t.libc not in self.tree[release][t.arch]:
            self.tree[release][t.arch][t.libc] = OrderedDict()
        if t.version not in self.tree[release][t.arch][t.libc]:
            self.tree[release][t.arch][t.libc][t.version] = []

        self.tree[release][t.arch][t.libc][t.version].append(t)
        self.list_by_release[release][t.name] = t

    def arch_list(self, release):
        return sorted(list(self.archs[release]))

    def libc_list(self, release):
        return sorted(list(self.libcs[release]))

    def version_list(self, release):
        return sorted(list(self.libcs[release]))

    def release_list(self):
        return sorted(list(self.tree.keys()))

    def get_tree(self, release):
        return self.tree[release]

    def get_by_arch_and_libc(self, release, arch, libc):
        toolchain_list = []
        if libc in self.tree[release][arch]:
            for v in self.tree[release][arch][libc]:
                toolchain_list += self.tree[release][arch][libc][v]
        return toolchain_list
