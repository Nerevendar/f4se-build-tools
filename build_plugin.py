import os, sys
from contextlib import contextmanager, suppress

#================================================================
# # About
# Plugin build script.
#
# # Arguments
# [1] BUILD_DIR - Location of the build folder.
# [2] PROJECT_DIR - Directory containing vcxproj file.
# [3] PLATFORM_TOOLSET - Toolset to compile the plugin with.
# [4] F4SE_REVISION - Which commit of F4SE to use for compilation.
# [5] COMMON_REVISION - Which commit of common to use for compilation.
#================================================================

#===================
# Configuration
#===================
# Get arguments
if len(sys.argv) > 3:
    BUILD_DIR        = sys.argv[1]
    PROJECT_DIR      = sys.argv[2]
    PLATFORM_TOOLSET = sys.argv[3]
    F4SE_REVISION    = sys.argv[4]
    COMMON_REVISION  = sys.argv[5]
else:
    print('FATAL: Invalid arguments.')
    sys.exit(1)

F4SE_REPO   = 'https://github.com/ianpatt/f4se.git'
COMMON_REPO = 'https://github.com/ianpatt/common.git'

# Location of files generated by build tools
BUILD_PROJECT  = os.path.join(PROJECT_DIR, 'build.vcxproj')
BUILD_SOLUTION = os.path.join(BUILD_DIR  , 'build.sln')

#===================
# Utilities
#===================
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(prevdir)
        
#===================
# Build
#===================
# Fetch F4SE
if not os.path.exists('{}/f4se'.format(BUILD_DIR)):
    # Recreate the structure of osvein/f4se-mirror
    os.system('git clone {} {}/f4se/src/f4se'.format(F4SE_REPO, BUILD_DIR))
    os.system('git clone {} {}/f4se/src/common --no-checkout'.format(COMMON_REPO, BUILD_DIR))
    with cd('{}/f4se/src/common'.format(BUILD_DIR)):
        os.system('git checkout {} -- common'.format(COMMON_REVISION))
f4se_dir = os.path.abspath('{}/f4se/src/f4se'.format(BUILD_DIR)).replace('\\', '/')
src_dir  = os.path.abspath('{}/f4se/src'.format(BUILD_DIR)).replace('\\', '/')

# Run build tools
BUILD_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
prepOK = 0 # exit code 0 == success
prepOK |= os.system('python {}/patch_f4se.py "{}"'.format(BUILD_TOOLS_DIR, f4se_dir))
prepOK |= os.system('python {}/update_project_references.py "{}" "{}" "{}"'.format(BUILD_TOOLS_DIR, PROJECT_DIR, f4se_dir, BUILD_PROJECT))
prepOK |= os.system('python {}/make_solution.py "{}" "{}"'.format(BUILD_TOOLS_DIR, PROJECT_DIR, BUILD_SOLUTION))

# Build project
buildOK = 1 # exit code 1 == failed
if prepOK == 0:
    os.environ['INCLUDE'] = '{};{};{}'.format(f4se_dir, src_dir, os.environ['INCLUDE'])
    buildOK = os.system('msbuild {} /p:PlatformToolset={} /p:UseEnv=true /p:Configuration=Release'.format(BUILD_DIR, PLATFORM_TOOLSET))
    
# Clean files generated by build tools
with suppress(FileNotFoundError):
    os.remove(BUILD_PROJECT)
    os.remove(BUILD_SOLUTION)

# Package plugin
if os.path.exists('dist'):
    PLUGIN_LOCATION_PATTERN = '{}/x64/Release/*.dll'.format(BUILD_DIR)
    DIST_DIR = 'dist'
    packageOK = os.system('python {}/package_plugin.py "{}" "{}" "{}" "{}"'.format(BUILD_TOOLS_DIR, PLUGIN_LOCATION_PATTERN, DIST_DIR, BUILD_DIR, PROJECT_DIR))

# Report result
sys.exit(buildOK)