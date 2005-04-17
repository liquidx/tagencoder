# instructions : python setup.py py2app (dist)
#                python setup.py py2app -A (alias/symlink/dev)

from distutils.core import setup
import py2app


plist = dict(
    CFBundleName = 'TagEncoder',
    CFBundleIconFile = 'TagEncoder.icns',
    CFBundleGetInfoString = '1.0 Copyright (c) 2005, Alastair Tse',
    CFBundleIdentifier = 'net.liquidx.tagencoder',
    CFBundleShortVersionString = '1.0',
    CFBundleVersion = '1.0',
    LSMinimumSystemVersion = '10.3.0',
    NSAppleScriptEnabled = 'No',
    )

py2app_options = dict(
    plist = plist
)


setup(
    app=['TagEncoder.py'],
    data_files=['Resources/English.lproj'],
#                'Resources/TagEncoder.icns'],
    options = dict(
        py2app=py2app_options
    ),
)
