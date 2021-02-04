#!/usr/bin/env python

from os import path
import hashlib
import json


def _is_package_reference(line):
    if line.startswith("#"):
        return False
    if "# disable GHA" in line:
        return False
    if "/sdk120" in line:
        return False
    if "/sdkARM" in line:
        return False
    if "/system" in line:
        return False
    if "@" in line:
        return False
    if "/" not in line:
        return False
    return True


def list_installed_packages(conan):
    installed_packages = []
    conan.search(["--json", "installed.json", "*"])
    installed = json.load(open("installed.json","r"))
    if installed["results"]:
        for p in installed["results"][0]["items"]:
            if _is_package_reference(p["recipe"]["id"]):
                installed_packages.append(p["recipe"]["id"])
    return installed_packages


class PackageReference(object):
    def _possible_conanfile_locations(self, name, version):
        return [
            path.join("recipes", name, version, "conanfile.py"),
            path.join("recipes", name, "all", "conanfile.py"),
        ]

    def __init__(self, conan, strref):
        self.conan = conan
        if "/" not in strref:
            raise RuntimeError("package reference '%s' does not contain slash" % strref)
        self.name, self.version = strref.split("/")
        self.conanfile_path = None
        for loc in self._possible_conanfile_locations(self.name, self.version):
            if path.isfile(loc):
                self.conanfile_path = loc
        if not self.conanfile_path:
            print("conanfile.py not found at %s" % self._possible_conanfile_locations)
            raise RuntimeError("Recipe for package %s could not be found" % (self.name + "/" + self.version))
        self.conanfile = open(self.conanfile_path, "rb").read()
        md5 = hashlib.md5()
        md5.update(self.conanfile)
        self.md5sum = md5.hexdigest()

    def export(self):
        self.conan.export([self.conanfile_path, self.name + "/" + self.version + "@_/_"])

    def __str__(self):
        return "name=%-16s\tver=%-16s\tmd5=%s\tsrc=%s" % (
            self.name,
            self.version,
            self.md5sum,
            self.conanfile_path
        )


class ConanfileTxt(object):
    def __init__(self, conan, filename):
        self.conan = conan
        self.packages = {}
        if path.isfile(filename):
            for line in open(filename, "rb").read().splitlines():
                strline = line.decode("ascii")
                if not _is_package_reference(strline):
                    continue
                package = PackageReference(conan, strline)
                self.packages[package.name] = package

    def export(self):
        for package in self.packages:
            package.export()
