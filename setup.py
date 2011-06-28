import os
import sys

from setup_cfg import *

VARS = {}
TOPDIR = os.path.abspath(os.path.dirname(__file__))
CLEAN = False
CORE = ['tokenize', 'parse', 'encode', 'py2bc']
MODULES = []

def main():
    chksize()
    if len(sys.argv) < 2:
        print HELP
        return
    
    global CLEAN
    CLEAN = 'clean' in sys.argv
    CLEAN = CLEAN
    
    get_libs()
    build_mymain()
    
    cmd = sys.argv[1]
    if cmd == 'build':
        build_gcc()
    elif cmd == 'devices':
        list_devs()
    elif cmd == 'install':
        install_all()
    elif cmd == 'shell':
        shell_dev()
    else:
        print 'invalid command'
        print HELP

HELP = """
## Droydypy help ##

python setup.py command [options] [modules]

Commands:
    build - build tinypy
    devices - list android devices attached
    install device_serial dest - install on your android [device_serial] at [dest]
    shell device_serial - open the shell of the specified [device_serial]

Options:
    clean - rebuild all .tpc during build
    
Modules:
    math - build math module

"""
def list_devs():
    do_cmd(ANDROID_ADB + " devices",  "#Fetching devices..")

def shell_dev():
    device = sys.argv[2]
    do_cmd(ANDROID_ADB + " -s " + device + " shell",  "#Opening " + device + "..")

def install_all():
    build = os.path.join(TOPDIR,  "build")
    device = sys.argv[2]
    dest = sys.argv[3]
    do_cmd(ANDROID_ADB + " -s " + device + " push " + build + " " + dest,  "#Installing..")

def do_cmd(cmd,  altxt = None):
    for k, v in VARS.items():
        cmd = cmd.replace(k, v)
    if '$' in cmd:
        print 'vars_error', cmd
        sys.exit(-1)
    
    if altxt == None:
        print cmd
    else:
        print altxt
    r = os.system(cmd)
    if r:
        print 'exit_status', r
        sys.exit(r)
        
def do_chdir(dest):
    print 'cd', dest
    os.chdir(dest)

def build_bc(opt=False):
    out = []
    for mod in CORE:
        out.append("""unsigned char tp_%s[] = {"""%mod)
        fname = mod + ".tpc"
        data = open(fname, 'rb').read()
        cols = 16
        for n in xrange(0, len(data), cols):
            out.append(", ".join([str(ord(v)) for v in data[n:n+cols]])+', ')
        out.append("""};""")
    out.append("")
    f = open('bc.c', 'wb')
    f.write('\n'.join(out))
    f.close()
                    
def py2bc(cmd, mod):
    src = '%s.py'%mod
    dest = '%s.tpc'%mod
    if CLEAN or not os.path.exists(dest) or os.stat(src).st_mtime > os.stat(dest).st_mtime:
        cmd = cmd.replace('$SRC', src)
        cmd = cmd.replace('$DEST', dest)
        do_cmd(cmd)
    else:
        print '#', dest, 'is up to date'

def gcc_cmd(olevel,  cfile,  outfile):
    cmd = ANDROID_GCC + " -Wall " + olevel + " -g " + cfile + " -I" + ANDROID_INCLUDE + " -L"
    cmd += ANDROID_LIB + " -nostdlib " + ANDROID_LIB + "crtbegin_dynamic.o" + " -lc -ldl -lm -o " + outfile
    return cmd

def build_gcc():
    mods = CORE[:]
    os.mkdir(os.path.join(TOPDIR, "build"))
    do_chdir(os.path.join(TOPDIR, 'tinypy'))

    for mod in mods:
        py2bc('python py2bc.py $SRC $DEST -nopos', mod)

    build_bc(True)

    do_cmd(gcc_cmd("",  "mymain.c",  "../build/tinypy"),  "#Compiling tinypy for Android...")
    do_chdir('..')

    print("# OK")
    
def get_libs():
    modules = os.listdir('modules')
    for m in modules[:]:
        if m not in sys.argv: modules.remove(m)
    global MODULES
    MODULES = modules

def build_mymain():
    src = os.path.join(TOPDIR, 'tinypy', 'tpmain.c')
    out = open(src, 'r').read()
    dest = os.path.join(TOPDIR, 'tinypy', 'mymain.c')
        
    vs = []
    for m in MODULES:
        vs.append('#include "../modules/%s/init.c"'%m)
    out = out.replace('/* INCLUDE */', '\n'.join(vs))
    
    vs = []
    for m in MODULES:
        vs.append('%s_init(tp);'%m)
    out = out.replace('/* INIT */', '\n'.join(vs))
    
    f = open(dest, 'w')
    f.write(out)
    f.close()
    return True

def shrink(fname):
    f = open(fname, 'r'); lines = f.readlines(); f.close()
    out = []
    fixes = [
    'vm', 'gc', 'params', 'STR', 
    'int', 'float', 'return', 'free', 'delete', 'init', 
    'abs', 'round', 'system', 'pow', 'div', 'raise', 'hash', 'index', 'printf', 'main']
    passing = False
    for line in lines:
        #quit if we've already converted
        if '\t' in line: return ''.join(lines)
        
        #change "    " into "\t" and remove blank lines
        if len(line.strip()) == 0: continue
        line = line.rstrip()
        l1, l2 = len(line), len(line.lstrip())
        line = "\t"*((l1-l2)/4)+line.lstrip()
        
        #remove comments
        if '.c' in fname or '.h' in fname:
            #start block comment
            if line.strip()[:2] == '/*':
                passing = True;
            #end block comment
            if line.strip()[-2:] == '*/':
               passing = False;
               continue
            #skip lines inside block comments
            if passing:
                continue
        if '.py' in fname:
            if line.strip()[:1] == '#': continue
        
        #remove the "namespace penalty" from tinypy ...
        for name in fixes:
            line = line.replace('TP_'+name, 't'+name)
            line = line.replace('tp_'+name, 't'+name)
        line = line.replace('TP_', '')
        line = line.replace('tp_', '')
        
        out.append(line)
    return '\n'.join(out)+'\n'
    
def chksize():
    t1, t2 = 0, 0
    for fname in [
        'tokenize.py', 'parse.py', 'encode.py', 'py2bc.py', 
        'tp.h', 'list.c', 'dict.c', 'misc.c', 'string.c', 'builtins.c', 
        'gc.c', 'ops.c', 'vm.c', 'tp.c', 'tpmain.c', 
        ]:
        fname = os.path.join(TOPDIR, 'tinypy', fname)
        f = open(fname, 'r'); t1 += len(f.read()); f.close()
        txt = shrink(fname)
        t2 += len(txt)
    print "#", t1, t2, t2-65536
    return t2


if __name__ == '__main__':
    main()
