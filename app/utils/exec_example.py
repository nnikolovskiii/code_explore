import math

tmp = "zzz"

def print_smth(message):
    print(message)

code_str = "print_smth('lol')\nprint(tmp)"
exec(code_str)
print("lol1")
