#!/usr/bin/env python

from os import path, environ, mkdir, chmod
import subprocess
import hashlib
import json


def conan_run(args):
    cmd = ['conan']
    if 'CONAN_DOCKER_IMAGE' in environ and environ['CONAN_DOCKER_IMAGE']:
        if not path.exists('.conan-docker'):
            mkdir('.conan-docker')
            chmod('.conan-docker', 0o777)
            chmod('sources', 0o777)
        cmd = ['docker', 'run',
               '-v', environ['GITHUB_WORKSPACE'] + '/sources:/home/conan/sources',
               '-v', environ['GITHUB_WORKSPACE'] + '/.conan-docker:/home/conan/.conan',
               environ['CONAN_DOCKER_IMAGE'],
               ] + cmd
    cmd += args
    subprocess.check_call(cmd)


def _is_gha_buildable(line):
    if line.startswith('#'):
        return False
    if '# GHA: ignore' in line:
        return False
    if '/system' in line:
        return False
    if '@' in line:
        return False
    if '/' not in line:
        return False
    return True


def list_installed_packages():
    installed_packages = []
    conan_run(['search', '--json', path.join('sources', 'installed.json'), '*'])
    installed = json.load(open(path.join('sources', 'installed.json'), 'r'))
    if installed['results']:
        for p in installed['results'][0]['items']:
            if _is_gha_buildable(p['recipe']['id']):
                installed_packages.append(p['recipe']['id'])
    return installed_packages


class PackageReference():
    def _possible_conanfile_locations(self):
        yield path.join('recipes', self.name, self.version, 'conanfile.py')
        full_ver = self.version.split('.')
        for i in range(len(full_ver) - 1, 0, -1):
            masked_ver = full_ver[:i] + ['x']
            yield path.join('recipes', self.name, '.'.join(masked_ver), 'conanfile.py')
        yield path.join('recipes', self.name, 'all', 'conanfile.py')

    def __init__(self, strref):
        if '# GHA: noexport' in strref:
            strref_stripped = strref[:strref.index('# GHA: noexport')].strip()
            self.export_recipe = False
        else:
            strref_stripped = strref.strip()
            self.export_recipe = True
        if '/' not in strref_stripped:
            raise RuntimeError('package reference `{ref}` does not contain slash'.format(ref=strref))
        self.name, self.version = strref_stripped.split('/')
        self.conanfile_path = None
        self.conanfile = ""
        self.md5sum = None
        if not self.export_recipe:
            return
        for loc in self._possible_conanfile_locations():
            print('searching for conanfile.py in {loc}'.format(loc=loc))
            if path.isfile(loc):
                self.conanfile_path = loc
                break
        if not self.conanfile_path:
            raise RuntimeError('Recipe for package {name}/{ver} could not be found'.format(
                name=self.name, ver=self.version))
        self.conanfile = open(self.conanfile_path, 'rb').read()
        md5 = hashlib.md5()
        md5.update(self.conanfile)
        self.md5sum = md5.hexdigest()

    def export(self):
        if self.export_recipe:
            conan_run(['export',
                       path.join('sources', self.conanfile_path),
                       self.name + '/' + self.version + '@_/_'])
        else:
            print('exporting recipe for {name}/{ver} is disabled in {txt}'.format(
                name=self.name, ver=self.version, txt=environ['CONAN_TXT']))

    def __str__(self):
        return 'name={name:<16}\tver={ver:<16}\tmd5={md5}\tsrc={src}'.format(
            name=self.name,
            ver=self.version,
            md5=self.md5sum,
            src=self.conanfile_path
        )


class ConanfileTxt():
    def __init__(self, filename, conanfile_required):
        self.packages = {}
        if path.isfile(filename):
            with open(filename) as f:
                for strline in f.read().splitlines():
                    if not _is_gha_buildable(strline):
                        continue
                    package = PackageReference(strline)
                    self.packages[package.name] = package
        elif conanfile_required:
            raise RuntimeError('File {filename} is required, but was not found')

    def export(self):
        for package in self.packages:
            package.export()
