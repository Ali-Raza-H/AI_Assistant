import os


def runLs():
    output = os.system("ls")
    return output

funcOut = runLs()

print(funcOut)
