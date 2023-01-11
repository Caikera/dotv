from dotv import *

def get_module_text_test():
    with open("./cmp_clbrt.v", 'r', encoding="utf-8") as vf:
        modules = get_module_text(vf)
        for module in modules:
            print("")
            for line in module:
                print(line)

def get_module_text_test_v():
    with open("./cmp_clbrt.v", 'r', encoding="utf-8") as vf:
        modules = get_module_text_2(vf)
        for module in modules:
            print("\n")
            for line in module:
                print(f"{line}", end="")
        print("\ndone")