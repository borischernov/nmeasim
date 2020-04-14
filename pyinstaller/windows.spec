# -*- mode: python -*-
from datetime import datetime
from importlib.metadata import metadata
from pathlib import Path

name = "nmeasim"
base_dir = Path.cwd()
build_dir = base_dir / "build"
build_dir.mkdir(exist_ok=True)
package_dir = base_dir / name

version_file = build_dir / "version_file"
version_info_file = build_dir / "version_info"
icon_file = package_dir / "icon.ico"
license_file = package_dir / "LICENSE"

meta = metadata(name)

with version_file.open('w') as fp:
    fp.write(meta["Version"])

exe_name = '{}-{}.exe'.format(meta["Name"], meta["Version"])

major, minor, patch, build = meta["Version"].split('.', 3)
build = build.split('dev', 1)[1].split('+', 1)[0]

version_string = f"{major}, {minor}, {patch}, {build}"
with license_file.open() as fp:
    copyright_line = fp.readline().strip()

version_info = "VSVersionInfo("
version_info += "ffi=FixedFileInfo("
version_info += f"filevers=({version_string}),"
version_info += f"prodvers=({version_string}),"
version_info += "mask=0x1f,"
version_info += "flags=0x0,"
version_info += "OS=0x4,"
version_info += "fileType=0x1,"
version_info += "subtype=0x0,"
version_info += "date=(0, 0)"
version_info += "),"
version_info += "kids=["
version_info += "StringFileInfo("
version_info += "["
version_info += "StringTable("
version_info += "'040904b0',"
version_info += "["
version_info += f"StringStruct('Comments', '{meta['Home-page']}'),"
version_info += f"StringStruct('CompanyName', '{meta['Author']}'),"
version_info += f"StringStruct('FileDescription', '{meta['Summary']}'),"
version_info += f"StringStruct('FileVersion', ''),"
version_info += f"StringStruct('InternalName', '{meta['Name']}'),"
version_info += f"StringStruct('LegalCopyright', '{copyright_line}'),"
version_info += f"StringStruct('OriginalFilename', '{exe_name}'),"
version_info += f"StringStruct('ProductName', '{meta['Name']}'),"
version_info += f"StringStruct('ProductVersion', '{version_string}')"
version_info += "]"
version_info += ")"
version_info += "]"
version_info += "),"
version_info += "VarFileInfo([VarStruct('Translation', [1033, 1200])])"
version_info += "]"
version_info += ")"

with version_info_file.open('w') as fp:
    fp.write(version_info)

a = Analysis(
    ['hook.py'],
    datas=[
        (str(icon_file), name),
        (str(license_file), name)
    ],
    hiddenimports=[],
    hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [
        (version_file.name, str(version_file), 'DATA'),
        ('u', '', 'OPTION')
    ],
    name=os.path.join('dist', exe_name),
    debug=False,
    strip=None,
    upx=True,
    console=True,
    version=str(version_info_file),
    icon=str(icon_file))
