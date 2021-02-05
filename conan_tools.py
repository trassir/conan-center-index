#!/usr/bin/env python

from os import path
import hashlib
import json


def _is_gha_buildable(line):
    if line.startswith("#"):
        return False
    if "# disable GHA" in line:
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
            if _is_gha_buildable(p["recipe"]["id"]):
                installed_packages.append(p["recipe"]["id"])
    return installed_packages


class PackageReference(object):
    def _possible_conanfile_locations(self):
        return [
            path.join("recipes", self.name, self.version, "conanfile.py"),
            path.join("recipes", self.name, "all", "conanfile.py"),
        ]

    def __init__(self, conan, strref):
        self.conan = conan
        if "/" not in strref:
            raise RuntimeError("package reference '{ref}' does not contain slash".format(ref=strref))
        self.name, self.version = strref.split("/")
        self.conanfile_path = None
        for loc in self._possible_conanfile_locations():
            if path.isfile(loc):
                self.conanfile_path = loc
                break
        if not self.conanfile_path:
            print("conanfile.py not found at {locs}".format(locs=self._possible_conanfile_locations()))
            raise RuntimeError("Recipe for package {pkg} could not be found".format(pkg=self.name + "/" + self.version))
        self.conanfile = open(self.conanfile_path, "rb").read()
        md5 = hashlib.md5()
        md5.update(self.conanfile)
        self.md5sum = md5.hexdigest()

    def export(self):
        self.conan.export([self.conanfile_path, self.name + "/" + self.version + "@_/_"])

    def __str__(self):
        return "name={name:<16}\tver={ver:<16}\tmd5={md5}\tsrc={src}".format(
            name=self.name,
            ver=self.version,
            md5=self.md5sum,
            src=self.conanfile_path
        )


class ConanfileTxt(object):
    def __init__(self, conan, filename, conanfile_required):
        self.conan = conan
        self.packages = {}
        if conanfile_required and not path.isfile(filename):
            raise RuntimeError("File {filename} is required, but was not found")
        with open(filename) as f:
            for strline in f.read().splitlines():
                if not _is_gha_buildable(strline):
                    continue
                package = PackageReference(conan, strline)
                self.packages[package.name] = package

    def export(self):
        for package in self.packages:
            package.export()
