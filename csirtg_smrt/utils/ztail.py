import os
import time

def open_wait(fn):
    while True:
        try:
            f = open(fn)
            return f
        except IOError:
            time.sleep(1)


def tail(fn):
    """Like tail -F """
    inode = stat_inode(fn)
    f = open_wait(fn)
    f.seek(0, 2)

    # Has the file inode changed
    changed = False
    while True:
        l = f.readline()
        if l:
            yield l
        elif changed:
            f.close()
            f = open_wait(fn)
            inode = os.fstat(f.fileno()).st_ino
            changed = False
        elif stat_inode(fn) != inode:
            #set changed to true, but then keep trying to read from the file to
            #check to see if it was written to after it was rotated.
            changed = True
        else:
            time.sleep(1)

def stat_inode(fn):
    try :
        return os.stat(fn).st_ino
    except OSError:
        return None

def multitail(filenames):
    """ tail multiple files, for each new line yield (filename, line) tuples"""
    files = {}
    for fn in filenames:
        try :
            handle = open(fn)
            handle.seek(0, 2)
            inode = os.fstat(handle.fileno()).st_ino
        except IOError:
            handle = None
            inode = None
        files[fn] = dict(handle=handle, inode=inode)

    while True:
        read = False
        for fn, info in files.items():
            l = info['handle'] and info['handle'].readline()
            if l:
                yield fn, l
                info['read'] = read = True
            else:
                info['read'] = False

        for fn, info in files.items():
            if not info['handle'] or (info['read'] == False and info['inode'] != stat_inode(fn)):
                if info['handle']:
                    info['handle'].close()
                try :
                    info['handle'] = open(fn)
                    info['inode'] = os.fstat(info['handle'].fileno()).st_ino
                except IOError:
                    info['handle'] = None
                    info['inode'] = None
        if not read:
            time.sleep(1)
