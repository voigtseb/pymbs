import os
import sys
import platform
from subprocess import Popen, PIPE, STDOUT


# f2py can be found in PYTHON_INSTALL_DIR/Scripts - must be in your path!

def compileF90(modulename, path, compiler=None):
    '''
    Compile fortran code generated by PyMbs to a python module. We experienced
    this to work best with the mingw32 compiler. Therefore it is hard coded
    below for windows. If you encounter problems or want to use another
    compiler, change the compiler variable according to your needs.
    '''
    modulename_py=modulename + "_compiledF90"
    try:
        #first delete
        if os.path.isfile(path + '/%s.pyd'%modulename_py):
            os.remove(path + '/%s.pyd'%modulename_py)
        
        # generate platform specific path to f2py and compiler defaults
        opsys = platform.system()

        if opsys == 'Windows':
            binpath = os.path.join(sys.prefix, 'python.exe')
            f2py = binpath + ' -m numpy.f2py'
            comp = '--compiler=mingw32 --skip-empty-wrappers' #--noopt'            

        elif opsys == 'Linux':
            binpath = sys.prefix+"/bin/"
            f2py = binpath + 'f2py'
            comp = ''

        else:
            binpath = ''   # assumes that f2py is somehow accessible from path
            comp = ''

        # use default compiler
        if compiler is None:
            compiler = comp
        #compiler += " --f90flags=-ffree-line-length-none"
        
        # Todo: try compiler flags to handle segfault error in functionmodule.f90
        # source: https://stackoverflow.com/questions/44633519/fortran-strange-segmentation-fault
        compiler += " --f90flags=\"-ffree-line-length-none -fno-stack-arrays -fno-realloc-lhs\""

        # compile
        f2py_call = str.format('{0} -c functionmodule.f90 {1}.f90 -m {2} {3}', 
                                f2py, modulename, modulename_py, compiler)
        print(path)
        print(f2py_call)

        compileProcess = Popen(f2py_call,
                               stdout=PIPE,
                               stderr=STDOUT, 
                               shell=True, 
                               cwd=path)

        while True:
            output = compileProcess.stdout.readline()[:-1]
            if output:
                print(output.decode('UTF-8'))
            if compileProcess.poll() is not None:
                break
        """
        output = compileProcess.communicate()

        if compileProcess.returncode != 0:
            print(output[0])
        else:
            print('Compilation of "%s.f90" successful' % modulename)
        """

    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)
        

def compileC(modulename, path):
    '''
    Compile C code generated by PyMbs to a python module. 
    Compilation on Linux is done by gcc which has to be in your PATH.

    On Windows, Visual Studio with cl.exe is used which must be in your PATH. 
    Additionally the folder containing the vcvars64.bat must be in your PATH 
    It is required to set up the developer console before compiling.
    Both files reside somewhere in the Visual Studio installation folder.
    '''

    # platform specifics
    opsys = platform.system()
    ext = 'dll' if opsys == 'Windows' else 'so'

    module_file = os.path.join(path, f'{modulename}.{ext}')

    try:
        #first delete existing module        
        if os.path.isfile(module_file):
            os.remove(module_file)

        if opsys == 'Windows':
            
            # Try gcc first on Windows, just less hassle
            compileProcess = compile_gcc(path, modulename)
            compileProcess.wait()

            # Fall back to Visual Studio if gcc was not found
            if compileProcess.returncode != 0:
                print("Trying Visual Studio...")
                compileProcess = compile_vs(path, modulename)
        
        else:
            # Use gcc on all other platforms    
            compileProcess = compile_gcc(path, modulename)

        output = compileProcess.communicate()

        if compileProcess.returncode != 0:
            print(output[0])
        else:
            print(f'Compilation of "{modulename}.c" successful')

    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)

    return module_file


def compile_gcc(path, modulename):
    """
    Use gcc to compile c-module to shared lib
    """    
    ext = 'dll' if platform.system() == 'Windows' else 'so'
    declspec = '-fdeclspec' if platform.system() == 'Darwin' else ''

    return Popen(f'gcc -Ofast -shared {modulename}.c -fPIC {declspec} -o {modulename}.{ext}',
                    stdout=PIPE, stderr=STDOUT, shell=True, cwd=path)


def compile_vs(path, modulename):
    """
    Use Visual Studio to compile c-module to shared lib
    """
    return Popen(f'vcvars64.bat && cl /LD {modulename}.c',
                    stdout=PIPE, stderr=STDOUT, shell=True, cwd=path)                    
