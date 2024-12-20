import re


def my_function(pattern):
    regex = re.compile(pattern)

    if regex.search("docs/optimum/v1.22.0/en/onnxruntime/quickstart"):
        print("lol")
    else:
        print("lol1")


my_function(r"v\d+(?:\.\d+)+")