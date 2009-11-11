"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup
import py2app
APP = ['itemgenerator.py']
DATA_FILES = ['style.css']
OPTIONS = dict(
    # iconfile='resources/myapp-icon.icns',
    argv_emulation=True,
    packages='wx',
    site_packages=True,
    semi_standalone=False,
    # resources=['resources/License.txt'],
    plist=dict(
        CFBundleName               = "ItemGenerator",
        CFBundleShortVersionString = "0.1.0",     # must be in X.X.X format
        CFBundleGetInfoString      = "ItemGenerator 0.1.0",
        CFBundleExecutable         = "ItemGenerator",
        CFBundleIdentifier         = "net.minrk.itemgenerator",
    )
)

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
# my patch for __boot__.py:
import os
import sys,shutil,glob
pjoin = os.path.join
bootfile = pjoin(".","dist","ItemGenerator.app","Contents","Resources","__boot__.py")
fp = open(bootfile)
boots = fp.read()
pyver = sys.version.split()[0][:3]
boots = boots.replace("""site.addsitedir(os.path.join(base, 'Python', 'site-packages'))""",
                """site.addsitedir(os.path.join(base, 'lib', 'python%s')) # add by Min"""%pyver)
fp = open(bootfile,'w')
fp.write(boots)
# sync Framework Python:
Contents=pjoin("./dist",OPTIONS['plist']['CFBundleExecutable']+'.app','Contents')
framedest=pjoin(Contents,'Frameworks/Python.framework/Versions')
if os.path.isdir(framedest):
    shutil.rmtree(framedest)
print Contents
print framedest
print "Copying Framework Python %s"%pyver
# print framedest
os.makedirs(framedest)
shutil.copytree("/System/Library/Frameworks/Python.framework/Versions/%s/"%pyver, pjoin(framedest, pyver),ignore=lambda _,__: ["Extras","test"])
print "stripping unneeded WX"
resourcelib=pjoin(Contents, "Resources/lib/python%s"%pyver)
wx = pjoin(resourcelib,"wx")
for subdir in "tools locale".split():
    shutil.rmtree(pjoin(wx, subdir))
for lib in glob.glob(pjoin(wx, "lib","*")):
    libname = os.path.basename(lib)
    if not libname.startswith("scrolledpanel") and not libname.startswith("__init__"):
        # print lib
        if os.path.isdir(lib):
            shutil.rmtree(lib)
        else:
            os.remove(lib)


print "stripping unneeded libs"
for lib in glob.glob(pjoin(resourcelib, "lib-dynload","_codec*")):
# for lib in glob.glob(pjoin(resourcelib,"_codec*")):
    os.remove(lib)
os.remove(pjoin(resourcelib,"lib-dynload","unicodedata.so"))


# for lib in "".split():
    # shutil.rmtree(pjoin(wx, "lib",lib))
