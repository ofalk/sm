import os


def modules_with_urls():
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    selfmod = os.path.basename(os.path.realpath(os.path.dirname(__file__)))
    # print(path)
    installed = []
    for module in os.listdir(path):
        if selfmod == module:
            continue
        if os.path.isfile(os.path.join(module, 'urls.py')):
            installed.append(module)
    return installed
