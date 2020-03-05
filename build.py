from os import environ
from sys import platform
from cpt.packager import ConanMultiPackager


if __name__ == "__main__":
    if platform == "darwin":
        builder = ConanMultiPackager(
            login_username="trassir-ci-bot",
            upload="https://api.bintray.com/conan/trassir/conan-public",
            upload_only_when_stable=1,
            stable_branch_pattern="cpt-username-channel-behavior",
            stable_channel="_",
            channel="_",
            username="_",
            remotes="https://api.bintray.com/conan/trassir/conan-public"
        )
    else:
        builder = ConanMultiPackager(
            login_username="trassir-ci-bot",
            upload="https://api.bintray.com/conan/trassir/conan-public",
            upload_only_when_stable=1,
            stable_branch_pattern="cpt-username-channel-behavior",
            stable_channel="_",
            remotes="https://api.bintray.com/conan/trassir/conan-public"
        )
    builder.add_common_builds(pure_c=False)
    builder.run()
