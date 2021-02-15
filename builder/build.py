#!/usr/bin/env python

from os import environ, mkdir, chdir, path
import subprocess
from environment import prepare_environment
from conan_tools import ConanfileTxt, list_installed_packages, conan_run


def print_section(message):
    print('=' * 80)
    print('   ' + message)
    print('=' * 80)


def collect_dependencies(branch_name):
    print_section('Collect packages info from branch {branch}'.format(branch=branch_name))
    mkdir(branch_name)
    chdir(branch_name)
    subprocess.check_call(['git', 'clone', environ['GITHUB_SERVER_URL'] + '/' + environ['GITHUB_REPOSITORY'], '.'])
    subprocess.check_call(['git', 'checkout', branch_name])
    subprocess.check_call(['git', 'branch'])
    conanfile_txt = ConanfileTxt(environ['CONAN_TXT'], branch_name != 'master')
    chdir('..')
    print('Collected {num} packages:'.format(num=len(conanfile_txt.packages)))
    for _, package in conanfile_txt.packages.items():
        print(package)
    return conanfile_txt


def detect_updated_packages(master_txt, branch_txt):
    '''
        Raise exception if following requirement is not satisfied:
        'updating conanfile.py must always be done with package version bump'
    '''
    inconsistent_update = False
    for name, package in branch_txt.packages.items():
        if name not in master_txt.packages.keys():
            print('CONAN_TXT: package added {pkg}'.format(pkg=package))
            continue
        if master_txt.packages[name].md5sum != package.md5sum:
            print('CONAN_TXT: recipe update detected\npackage(master): {pkg_master}\npackage(branch): {pkg_branch}'.format(
                pkg_master=master_txt.packages[name],
                pkg_branch=package))
            if master_txt.packages[name].version == package.version:
                inconsistent_update = True
                print('CONAN_TXT: recipe updated but version did not')
        else:
            if master_txt.packages[name].version == package.version:
                print('CONAN_TXT: package did not change: {name}/{ver}'.format(
                    name=package.name, ver=package.version))
            else:
                print('CONAN_TXT: package updated with no recipe changes: {ref_master} => {ref_branch}'.format(
                    ref_master=master_txt.packages[name].name + '-' + master_txt.packages[name].version,
                    ref_branch=package.name + '-' + package.version))
        if inconsistent_update:
            raise RuntimeError('package recipe updated but version did not')


def detect_dependency_lock(installed, conanfile_txt_head):
    '''
        Raise exception if .txt file does not contain entire dependency tree
    '''
    txt_needs_updating = False
    for pi in installed:
        name, version = pi.split('/')
        if name not in conanfile_txt_head.packages:
            print('Package {name}/{version} is not mentioned in {txt}'.format(
                name=name, version=version, txt=environ['CONAN_TXT']))
            txt_needs_updating = True
            continue
        if version != conanfile_txt_head.packages[name].version:
            print('Package {name}/{ver} is mentioned in {txt} with different version {name}/{ver_txt}'.format(
                name=name, ver=version, txt=environ['CONAN_TXT'], ver_txt=conanfile_txt_head.packages[name].version))
            txt_needs_updating = True
            continue
        print('Package {name} is confirmed by {txt} as {name}/{ver}'.format(
            name=name, txt=environ['CONAN_TXT'], ver=version))
    if txt_needs_updating:
        raise RuntimeError('{txt} needs updating, see packages listed above'.format(
            txt=environ['CONAN_TXT']))


if __name__ == '__main__':
    upload_remote = prepare_environment()

    conanfile_txt_master = collect_dependencies('master')
    if 'GITHUB_HEAD_REF' in environ and environ['GITHUB_HEAD_REF'] != '':
        conanfile_txt_head = collect_dependencies(environ['GITHUB_HEAD_REF'])
    else:
        conanfile_txt_head = conanfile_txt_master

    print_section('Ensure recipe changes accompanied with version bump')
    detect_updated_packages(conanfile_txt_master, conanfile_txt_head)

    print_section('Exporting all package recipes referenced in {txt}'.format(txt=environ['CONAN_TXT']))
    for _, package in conanfile_txt_head.packages.items():
        package.export()

    print_section('Building packages from {txt} for {profile} - {build_type}'.format(
        txt=environ['CONAN_TXT'],
        profile=environ['CONAN_PROFILE'],
        build_type=environ['CONAN_BUILD_TYPE']
    ))
    conan_run(['install', path.join('sources', environ['CONAN_TXT']),
               '-if', 'install_dir',
               '-pr', path.join('sources', environ['CONAN_PROFILE']),
               '-s', 'build_type={build}'.format(build=environ['CONAN_BUILD_TYPE']),
               '--build', 'missing'])

    print_section('Enumerating installed packages')
    installed = list_installed_packages()

    print_section('Ensure all packages have mention in {txt}'.format(txt=environ['CONAN_TXT']))
    detect_dependency_lock(installed, conanfile_txt_head)

    print_section('Uploading packages')
    if installed:
        conan_run(['upload', '--confirm', '--force', '--all', '-r', upload_remote, '*'])
