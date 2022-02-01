#!/usr/bin/env python3
r"""
                     _  __ _       _     _     _
                    (_)/ _(_)     | |   (_)   | |
  ((.))    __      ___| |_ _ _ __ | |__  _ ___| |__   ___ _ __
    |      \ \ /\ / / |  _| | '_ \| '_ \| / __| '_ \ / _ \ '__|
   /_\      \ V  V /| | | | | |_) | | | | \__ \ | | |  __/ |
  /___\      \_/\_/ |_|_| |_| .__/|_| |_|_|___/_| |_|\___|_|
 /     \                    | |
                            |_|  Version {}
"""


import os
import sys
import shutil
import tempfile
from textwrap import dedent
import distutils.sysconfig
import distutils.ccompiler
from distutils.errors import CompileError, LinkError
from distutils.command.build_ext import build_ext
from setuptools import Command, find_packages, setup, Extension
from setuptools.command.install import install
from roguehostapd.buildutil import build_files


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system("rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info")


# code for checking if libnl-dev and libnl-genl-dev exist
LIBNL_CODE = dedent(
    """
#include <netlink/netlink.h>
#include <netlink/genl/genl.h>
int main(int argc, char* argv[])
{
   struct nl_msg *testmsg;
   testmsg = nlmsg_alloc();
   nlmsg_free(testmsg);
   return 0;
}
"""
)

# code for checking if openssl library exist
OPENSSL_CODE = dedent(
    """
#include <openssl/ssl.h>
#include <openssl/err.h>
int main(int argc, char* argv[])
{
    SSL_load_error_strings();
    return 0;
}
"""
)

LIBNAME_CODE_DICT = {"netlink": LIBNL_CODE, "openssl": OPENSSL_CODE}


def check_required_library(libname, libraries=None, include_dir=None):
    build_success = True
    tmp_dir = tempfile.mkdtemp(prefix="tmp_" + libname + "_")
    bin_file_name = os.path.join(tmp_dir, "test_" + libname)
    file_name = bin_file_name + ".c"
    with open(file_name, "w") as filep:
        filep.write(LIBNAME_CODE_DICT[libname])
    compiler = distutils.ccompiler.new_compiler()
    distutils.sysconfig.customize_compiler(compiler)
    try:
        compiler.link_executable(
            compiler.compile([file_name], include_dirs=include_dir),
            bin_file_name,
            libraries=libraries,
        )
    except CompileError:
        build_success = False
    except LinkError:
        build_success = False
    finally:
        shutil.rmtree(tmp_dir)
    if build_success:
        return True
    err_msg = (
        "The development package for "
        + libname
        + " is required "
        + "for the compilation of roguehostapd. "
        + "Please install it and "
        + "rerun the script (e.g. on Debian-based systems "
        "run: apt-get install "
    )
    if libname == "openssl":
        err_msg += "libssl-dev"
    else:
        err_msg += "libnl-3-dev libnl-genl-3-dev"
    sys.exit(err_msg)


def get_extension_module():
    ext_module = Extension(build_files.SHARED_LIB_PATH,
                           define_macros=build_files.HOSTAPD_MACROS,
                           libraries=['rt', 'ssl', 'crypto', 'nl-3', 'nl-genl-3'],
                           sources=build_files.get_all_source_files(),
                           include_dirs=[build_files.HOSTAPD_SRC,
                                         build_files.HOSTAPD_UTILS,
                                         build_files.LIB_NL3_PATH])

    return [ext_module]

def check_dnsmasq():
    if not os.path.isfile("/usr/sbin/dnsmasq"):
        sys.exit(
            "dnsmasq not found in /usr/sbin/dnsmasq. "
            + "Please install dnsmasq and rerun the script "
            + "(e.g. on Debian-based systems: "
            + "apt-get install dnsmasq)"
        )


print()
requirements = open("requirements.txt", "r")
# setup settings
NAME = "wifiphisher"
AUTHOR = "me@theman"
AUTHOR_EMAIL = "me@theman"
DESCRIPTION = "Automated phishing attacks against Wi-Fi networks"
LICENSE = "GPL"
KEYWORDS = ["wifiphisher", "evil", "twin", "phishing"]
PACKAGES = find_packages(exclude=["docs", "tests"])
PACKAGE_DIR = {"wifiphisher": "wifiphisher"}
PACKAGE_DATA = {
    "wifiphisher": [
        "roguehostapd/config/hostapd.conf",
        "roguehostapd/config/config.ini",
        "pyric/nlhelp/*.help",
        "pyric/utils/data/*.txt",
    ]
}
INCLUDE_PACKAGE_DATA = True
VERSION = "1.4"
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Intended Audience :: Information Technology",
]
ENTRY_POINTS = {"console_scripts": [
    "wifiphisher = wifiphisher.pywifiphisher:run"]}
INSTALL_REQUIRES = requirements.readlines()
CMDCLASS = {"clean": CleanCommand, "install": install, "build_ext": build_ext}
LIB_NL3_PATH = "/usr/include/libnl3"
LIB_SSL_PATH = "/usr/include/openssl"
EXT_MODULE = get_extension_module()
check_dnsmasq()
check_required_library("netlink", ["nl-3", "nl-genl-3"], [LIB_NL3_PATH])
check_required_library("openssl", ["ssl"], [LIB_SSL_PATH])
shutil.rmtree("tmp")

setup(
    name=NAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    license=LICENSE,
    keywords=KEYWORDS,
    packages=PACKAGES,
    package_dir=PACKAGE_DIR,
    package_data=PACKAGE_DATA,
    include_package_data=INCLUDE_PACKAGE_DATA,
    version=VERSION,
    entry_points=ENTRY_POINTS,
    install_requires=INSTALL_REQUIRES,
    classifiers=CLASSIFIERS,
    cmdclass=CMDCLASS,
    ext_modules=EXT_MODULE
)
print(__doc__.format(VERSION))
