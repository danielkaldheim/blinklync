### makeapplication.py
from bundlebuilder import buildapp

buildapp(
    name='Blinklync.app', # what to build
    mainprogram='lync.py', # your app's main()
    argv_emulation=1, # drag&dropped filenames show up in sys.argv
    iconfile='myapp.icns', # file containing your app's icons
    standalone=1, # make this app self contained.
    includeModules=[], # list of additional Modules to force in
    includePackages=[], # list of additional Packages to force in
    libs=[], # list of shared libs or Frameworks to include
)

### end of makeapplication.py
