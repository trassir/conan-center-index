from os import environ
from sys import platform
from cpt.packager import ConanMultiPackager


if __name__ == "__main__":
    if platform == "darwin":
        os.environ["CONAN_USERNAME"] = "_"
        os.environ["CONAN_CHANNEL"] = "_"
    else:
        if not environ["CONAN_REFERENCE"].endswith("@/"):
            os.environ["CONAN_REFERENCE"] += "@/"
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
