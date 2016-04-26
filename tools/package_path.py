import sys
import re

if __name__ == '__main__':
    paths = []
    sys_paths = sys.path
    rex1 = ".*/dist-packages[/]?$"
    rex2 = ".*/site-packages[/]?$"
    for sys_path in sys_paths:
        if re.match(rex1, sys_path) or re.match(rex2, sys_path):
            paths.append(sys_path)
    
    if not paths:
        print ""
        sys.exit(0)
    for path in paths:
        if "local" in path:
            print path
            sys.exit(0)
    print paths[0]
