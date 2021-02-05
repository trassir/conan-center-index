from os import environ, path, mkdir, chdir
import sys
import subprocess
from environment import  prepare_environment
from conan_tools import ConanfileTxt, list_installed_packages


def print_section(message):
    print("=" * 80)
    print("   " + message)
    print("=" * 80)


def collect_dependencies(branch_name):
    print_section("Collect packages info from branch {branch}".format(branch=branch_name))
    mkdir(branch_name)
    chdir(branch_name)
    subprocess.check_call(["git", "clone", environ["GITHUB_SERVER_URL"] + "/" + environ["GITHUB_REPOSITORY"], "."])
    subprocess.check_call(["git", "checkout", branch_name])
    subprocess.check_call(["git", "branch"])
    conanfile_txt = ConanfileTxt(conan, environ["CONAN_TXT"], branch_name != "master")
    chdir("..")
    print("Collected {num} packages:".format(num=len(conanfile_txt.packages)))
    for _, package in conanfile_txt.packages.items():
        print(package)
    return conanfile_txt


def detect_updated_packages(master_txt, branch_txt):
    """
        Raise error if following requirement is not satisfied:
        "updating conanfile.py must always be done with package version bump"
    """
    for name, package in branch_txt.packages.items():
        if name not in master_txt.packages.keys():
            print("CONAN_TXT: package added {pkg}".format(pkg=package))
            continue
        if master_txt.packages[name].md5sum != package.md5sum:
            print("CONAN_TXT: recipe update detected\npackage(master): {pkg_master}\npackage(branch): {pkg_branch}".format(
                pkg_master=master_txt.packages[name],
                pkg_branch=package))
            if master_txt.packages[name].version == package.version:
                raise RuntimeError("package recipe updated but version did not")
        else:
            if master_txt.packages[name].version == package.version:
                print("CONAN_TXT: package did not change: {name}-{ver}".format(
                    name=package.name, ver=package.version))
            else:
                print("CONAN_TXT: package updated with no recipe changes: {ref_master} => {ref_branch}".format(
                    ref_master=master_txt.packages[name].name + "-" + master_txt.packages[name].version,
                    ref_branch=package.name + "-" + package.version))


if __name__ == "__main__":
    conan, upload_remote = prepare_environment()

    conanfile_txt_master = collect_dependencies("master")
    conanfile_txt_head = collect_dependencies(environ.get("GITHUB_HEAD_REF"))

    print_section("Ensure recipe changes accompanied with version bump")
    detect_updated_packages(conanfile_txt_master, conanfile_txt_head)

    print_section("Exporting all package recipes referenced in {txt}".format(txt=environ["CONAN_TXT"]))
    for _, package in conanfile_txt_head.packages.items():
        package.export()

    for build_type in ["Debug", "Release"]:
        print_section("Building packages for build_type={build}".format(build=build_type))
        conan.install([environ["CONAN_TXT"],
                    "-if", "install_dir",
                    "-pr", environ["CONAN_PROFILE"],
                    "-s", "build_type={build}".format(build=build_type),
                    "--build", "missing"])

    print_section("Enumerating installed packages")
    installed = list_installed_packages(conan)

    print_section("Ensure all packages have mention in {txt}".format(txt=environ["CONAN_TXT"]))
    for pi in installed:
        name, version = pi.split("/")
        if name not in conanfile_txt_head.packages:
            raise RuntimeError("Package {name} is not mentioned in {txt}".format(name=name, txt=environ["CONAN_TXT"]))
        if version != conanfile_txt_head.packages[name].version:
            raise RuntimeError("Package {name}-{ver} mentioned in {txt} with different version {name}-{ver_txt}".format(
                name=name, ver=version, txt=environ["CONAN_TXT"], ver_txt=conanfile_txt_head.packages[name].version))
        package_txt = conanfile_txt_head.packages[name]
        print("Package {name} is confirmed by {txt} as {name}-{ver}".format(
            name=name, txt=environ["CONAN_TXT"], ver=version))

    print_section("Uploading packages")
    if installed:
        conan.upload(["--confirm", "--force", "--all", "-r", upload_remote, "*"])
