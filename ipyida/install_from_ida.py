# -*- encoding: utf8 -*-
#
# Automate the installation of pip and IPyIDA.
#
# Copyright (c) 2016-2018 ESET
# Author: Marc-Etienne M.Léveillé <leveille@eset.com>
# See LICENSE file for redistribution.

import idaapi
import os
import sys
from contextlib import contextmanager
import tempfile
import subprocess
import fileinput
import pkg_resources
import shutil

if not "IPYIDA_PACKAGE_LOCATION" in dir():
    IPYIDA_PACKAGE_LOCATION = "https://github.com/eset/ipyida/archive/stable.tar.gz"


# Fix the sys.exectuable path. It's misleading in two cases:
#  - On Windows, it's set to 'idaq.exe'.
#  - If a virtualenv is activated with activate_this.py, sys.prefix is changed
#    but sys.executable is still set to the original process. pip and packages
#    will not install in the virtualenv if we don't set it right.
if not hasattr(sys, 'real_executable'):
    sys.real_executable = sys.executable
    if sys.platform == 'win32':
        sys.executable = os.path.join(sys.prefix, 'Python.exe')
    else:
        sys.executable = os.path.join(sys.prefix, 'bin', 'python')

# IDA Python sets sys.stdout to a file-like object IDAPythonStdOut. It doesn't
# have things like fileno, close, etc. This helper uses a file and redirect the
# content back to IDA's stdout.
@contextmanager
def temp_file_as_stdout():
    ida_stdout = sys.stdout
    try:
        with tempfile.TemporaryFile() as f:
            sys.stdout = f
            yield
            f.seek(0)
            ida_stdout.write(f.read())
    finally:
        sys.stdout = ida_stdout

try:
    import pip
    print("[+] Using already installed pip (version {:s})".format(pip.__version__))
except ImportError:
    print("[+] Installing pip")
    import urllib2

    if sys.hexversion < 0x02070900:
        # There are SSL problems with Python version < 2.7.9
        # See https://github.com/eset/ipyida/issues/11
        print("[-] IPyIDA installer requires Python 2.7.9 or newer")
        raise Exception("Python >= 2.7.9 required")

    get_pip = urllib2.urlopen("https://bootstrap.pypa.io/get-pip.py").read()
    with temp_file_as_stdout():
        p = subprocess.Popen(
            sys.executable,
            stdin=subprocess.PIPE,
            stdout=sys.stdout
        )
        p.communicate(get_pip)
    try:
        import pip
    except:
        print("[-] Could not install pip.")
        raise

def pip_install(package, extra_args=[]):
    pip_install_cmd = [ sys.executable, "-m", "pip", "install", "--upgrade" ]
    with temp_file_as_stdout():
        p = subprocess.Popen(
            pip_install_cmd + extra_args + [ package ],
            stdin=subprocess.PIPE,
            stdout=sys.stdout
        )
        ret = p.wait()
    return ret

if pip_install(IPYIDA_PACKAGE_LOCATION) != 0:
    print("[.] ipyida system-wide package installation failed, trying user install")
    if pip_install(IPYIDA_PACKAGE_LOCATION, [ "--user" ]) != 0:
        raise Exception("ipyida package installation failed")

if not os.path.exists(idaapi.get_user_idadir()):
    os.makedirs(idaapi.get_user_idadir(), 0755)

ida_python_rc_path = os.path.join(idaapi.get_user_idadir(), "idapythonrc.py")
rc_file_content = ""

if os.path.exists(ida_python_rc_path):
    with file(ida_python_rc_path, "r") as rc:
        rc_file_content = rc.read()

if "# BEGIN IPyIDA loading" in rc_file_content:
    print("[.] Old IPyIDA loading script present in idapythonrc.py. Removing.")
    in_ipyida_block = False
    for line in fileinput.input(ida_python_rc_path, inplace=1, backup='.ipyida_old'):
        if line.startswith("# BEGIN IPyIDA loading code"):
            in_ipyida_block = True
        elif line.startswith("# END IPyIDA loading code"):
            in_ipyida_block = False
        elif not in_ipyida_block:
            sys.stdout.write(line)

ipyida_stub_target_path = os.path.join(idaapi.get_user_idadir(), "plugins", "ipyida.py")
if not os.path.exists(os.path.dirname(ipyida_stub_target_path)):
    os.makedirs(os.path.dirname(ipyida_stub_target_path), 0755)

shutil.copyfile(
    pkg_resources.resource_filename("ipyida", "ipyida_plugin_stub.py"),
    ipyida_stub_target_path
)
print("[+] ipyida.py added to user plugins")

idaapi.load_plugin('ipyida.py')

if os.name == 'nt':
    # No party for Windows
    print("[+] IPyIDA Installation successful. Use <Shift+.> to open the console.")
else:
    print("[🍺] IPyIDA Installation successful. Use <Shift+.> to open the console.")
