from os import environ
from sys import platform
from cpt.packager import ConanMultiPackager
from cpt.tools import get_bool_from_env


if __name__ == "__main__":
    environ["CONAN_USERNAME"] = "_"
    environ["CONAN_CHANNEL"] = "ci"

    if "CONAN_OPTIONS" in environ and environ["CONAN_OPTIONS"] != "":
        environ["CONAN_OPTIONS"] = "*:shared=True," + environ["CONAN_OPTIONS"]
    else:
        environ["CONAN_OPTIONS"] = "*:shared=True"

    conan_config_url = None
    if platform != "linux":
        conan_config_url="https://github.com/trassir/conan-config.git"

    stable_branch_pattern = "master"
    upload = ("https://api.bintray.com/conan/trassir/conan-public", True, "bintray-trassir")
    if "GITHUB_HEAD_REF" in environ:
        head_ref = environ["GITHUB_HEAD_REF"]
        print(head_ref)
        stable_branch_pattern = head_ref
        upload = ("https://api.bintray.com/conan/trassir/conan-staging", True, "bintray-trassir")

    is_pure_c = get_bool_from_env('IS_PURE_C')
    builder = ConanMultiPackager(
        login_username="trassir-ci-bot",
        upload=upload,
        upload_only_when_stable=1,
        stable_branch_pattern=stable_branch_pattern,
        stable_channel="_",
        config_url=conan_config_url,
        remotes="https://api.bintray.com/conan/trassir/conan-public"
    )
    builder.add_common_builds(shared_option_name=False, pure_c=is_pure_c)
    builder.run()

# rebuild everything 7
