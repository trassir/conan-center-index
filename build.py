import os
import re
from cpt.printer import Printer
from cpt.ci_manager import CIManager
from cpt.packager import ConanMultiPackager
from cpt.tools import get_bool_from_env

KNOWN_ARM_PLATFORMS = [
    'hi3520dv300',
    'hi3521av100',
    'hi3521dv100',
    'hi3531av100',
    'hi3531d',
    'hi3536',
    'hi3536c',
    'hi3536dv100',
]
STABLE_BRANCH = "master"

def get_arm_platforms():
    env = os.getenv('ARM_PLATFORMS')
    if not env:
        return None
    if env == 'all':
        return KNOWN_ARM_PLATFORMS
    platforms = env.split(' ')
    for p in platforms:
        if p not in KNOWN_ARM_PLATFORMS:
            raise RuntimeError("'{}': unknown ARM platform".format(p))
    return platforms


def main():
    # conan converts '_' into None so we need to provide a stub username
    ci = CIManager(Printer())
    if ci.is_pull_request() or re.compile(STABLE_BRANCH).match(ci.get_branch()):
        os.environ["CONAN_USERNAME"] = "_"
    else:
        os.environ["CONAN_USERNAME"] = "trassir"
    os.environ["CONAN_CHANNEL"] = "ci"

    is_pure_c = get_bool_from_env('IS_PURE_C')
    arm_platforms = get_arm_platforms()
    is_arm = bool(arm_platforms)
    remotes = ["https://api.bintray.com/conan/trassir/conan-public"]

    builder = ConanMultiPackager(
        login_username="trassir-ci-bot",
        upload="https://api.bintray.com/conan/trassir/conan-public",
        upload_only_when_stable=1,
        stable_branch_pattern="master",
        stable_channel="_",
        # remotes=remotes
    )
    if not is_arm:
        builder.add_common_builds(pure_c=is_pure_c)
        builder.run()
    else:
        # cannot rely on add_common_builds since compiler.version and arch are taken from profile instead of envvars
        for bt in os.getenv('CONAN_BUILD_TYPES').split(','):
            builder.add(settings=dict(build_type=bt))
        for platform in arm_platforms:
            os.environ['CONAN_DEFAULT_PROFILE_PATH']="/home/conan/.conan/profiles/%s"%platform
            builder.run()

if __name__ == "__main__":
    main()
