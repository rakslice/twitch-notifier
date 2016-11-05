#!/usr/bin/python
import os
from distutils.core import setup
import py2exe
import sys

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
<assemblyIdentity
    version="0.64.1.0"
    processorArchitecture="x86"
    name="Controls"
    type="win32"
/>
<description>rakslice's twitch-notifier</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.30729.4918"
            processorArchitecture="X86"
            publicKeyToken="1fc8b3b9a1e18e3b"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""

"""
installs manifest and icon into the .exe
but icon is still needed as we open it
for the window icon (not just the .exe)
changelog and logo are included in dist
"""

from glob import glob


def main():

    program_files_x86 = os.environ["ProgramFiles(x86)"]
    assert os.path.isdir(program_files_x86)
    vs2008_base_dir = os.path.join(program_files_x86, "Microsoft Visual Studio 9.0")
    assert os.path.isdir(vs2008_base_dir)
    vs2008_crt_redist_dir = os.path.join(vs2008_base_dir, "VC", "redist", "x86", "Microsoft.VC90.CRT")
    assert os.path.isdir(vs2008_crt_redist_dir)
    assert not vs2008_crt_redist_dir.endswith("\\")
    msvcrt_data_files_proper = glob(vs2008_crt_redist_dir + r'\*.*')

    assert len(msvcrt_data_files_proper) == 4, msvcrt_data_files_proper
    msvcrt_data_files = [("Microsoft.VC90.CRT", msvcrt_data_files_proper)]

    sys.path.append(vs2008_crt_redist_dir)

    setup(
            # windows=[
            console=[
                {
                    "script": "notifiergui/notifier_gui_main.py",
                    "icon_resources": [(1, "assets/icon.ico")],
                    "other_resources": [(24, 1, manifest)]
                }
            ],
            data_files=["assets/icon.ico"] + msvcrt_data_files,
            options={'py2exe': {
                                # 'excludes': 'gevent._socket3',
                                'bundle_files': 2,
                                'packages': [
                                    # Removed these because I am testing without grequests
                                    # 'grequests',
                                    # 'gevent.builtins',
                                    'md5',
                                    'socket',
                                    # 'sys',  # causes failure
                                    # 'time',
                                    'encodings',
                                    'os',
                                    'dbhash',
                                    'urllib2',
                                    'twitch',
                                    'six',
                                    'ssl',
                                             ],
                                }},
    )


if __name__ == "__main__":
    main()
