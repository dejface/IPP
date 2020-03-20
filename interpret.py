import xml.etree.ElementTree as ET
import argparse
import sys

hashTable = {}
stackOfFrames = list()

def arg_handler():
    argsparser = argparse.ArgumentParser(description="Loads XML code, transforms it to IPPcode20 and executes it")
    argsparser.add_argument("--source", nargs=1, help="Input file with XML code")
    argsparser.add_argument("--input", nargs=1, help="File with inputs(f.e. instruction READ)")

    args = argsparser.parse_args()

    if args.input is None and args.source is None:
        sys.exit(10)

    try:
        if args.input is None:
            inputFile = sys.stdin
        else:
            inputFile = open(args.input[0], "r")

        if args.source is None:
            sourceFile = sys.stdin
        else:
            sourceFile = open(args.source[0], "r")
    except:
        sys.exit(11)

    return (sourceFile, inputFile)


def readSource(sourceFile):
    dictOfIntructions = dict()
    okCheck = False
    tree = ET.parse(sourceFile).getroot()
    for attrib, item in tree.attrib.items():
        if attrib == "language" and item == "IPPcode20":
            okCheck = True
        else:
            sys.exit(32)
    if not okCheck:
        sys.exit(32)

    for instruction in tree:
        order = instruction.attrib["order"]
        opcode = instruction.attrib["opcode"]

        if opcode == "none" or order is None:
            sys.exit(32)

        types = ["string", "int", "var", "type", "nil", "bool", "label"]
        instructions = dict()
        instructions[int(order)] = list()
        args = list()
        for i in range(len(instruction)):
            xmlArg = instruction.find("arg"+str(i+1))
            if xmlArg.attrib["type"] not in types:
                exit(53)
            arg = (xmlArg.attrib["type"], xmlArg.text)
            args.append(arg)
            #TODO osetrit lepsie XML napr.type apod.
        instructions[int(order)].append(opcode)
        instructions[int(order)].append(args)
        dictOfIntructions.update(instructions)
    dictOfIntructions = sorted(dictOfIntructions.items(), key=lambda x: x[0])

    return dictOfIntructions

def checkSymb(var):
    if var == 'string' or var == 'int' or var == 'bool' or var == 'nil':
        return True
    else:
        return False

def editVar(var):
    if var.find("@") == -1:
        sys.exit(53)
    else:
        prefix = var[:2]
        suffix = var[3:]

    return prefix, suffix

def mySwitch(argument):
    switcher = {"MOVE": move,
              "CREATEFRAME": createframe,
              "PUSHFRAME": pushframe,
              "POPFRANE": popframe,
              "DEFVAR": defvar,
              "CALL": call,
              "ADD": add,
              "SUB": sub,
              "MUL": mul,
              "IDIV": idiv}
    execs = switcher.get(argument[1][0], lambda: "Wrong instruction!\n")
    return execs(argument[1])


def move(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)
    if checkSymb(argument[1][1][0]) is False:
        sys.exit(32)
    # TODO overit definovanost v hashtable
    destPrefix, destSuffix = editVar(argument[1][0][1])
    srcPrefix, srcSuffix = argument[1][1]
    var = (srcPrefix, srcSuffix)

    hashTable[destPrefix][destSuffix] = var
    print(hashTable)

# creates a temporary frame TF

def createframe(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)
    hashTable["TF"] = {}

# pushes TF to stackOfFrames which means it will be covered by LF,
# if TF doeasn't exists, error will be raised

def pushframe(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)
    if "TF" not in hashTable:
        sys.exit(55)
    if "LF" in hashTable:
        stackOfFrames.append(hashTable["LF"])   # appending frame to stack
    hashTable["LF"] = hashTable.pop("TF")   # frame TF is replaced by LF

# pops a frame TODO

def popframe(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)
    if "LF" not in hashTable:
        sys.exit(55)
    hashTable["TF"] = hashTable.pop("LF")
    if len(stackOfFrames) >= 1:
        hashTable["LF"] = stackOfFrames.pop()


# defines variable var in a specific frame

def defvar(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)

    if (argument[1][0][0]) != 'var':
        sys.exit(32)
    prefix, suffix = editVar(argument[1][0][1])
    #TODO errory
    hashTable[prefix][suffix] = None


def call(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)
    pass
    #var = argument[1]

    #hashTable["label"][var]
    #TODO

def add(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if (argument[1][0][0]) != 'var':
        sys.exit(32)

    if (argument[1][1][0] != 'int') and (argument[1][2][0] != 'int'):
        sys.exit(53)

    destPrefix, destSuffix = editVar(argument[1][0][1])

    result = int(argument[1][1][1]) + int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

def sub(argument):
    # TODO aj v add overit definovanost v tabulke a ak by nebol type int ale var
    if (len(argument[1])) != 3:
        sys.exit(32)

    if (argument[1][0][0]) != 'var':
        sys.exit(32)

    if (argument[1][1][0] != 'int') and (argument[1][2][0] != 'int'):
        sys.exit(53)

    destPrefix, destSuffix = editVar(argument[1][0][1])

    result = int(argument[1][1][1]) - int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

def mul(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if (argument[1][0][0]) != 'var':
        sys.exit(32)

    if (argument[1][1][0] != 'int') and (argument[1][2][0] != 'int'):
        sys.exit(53)

    destPrefix, destSuffix = editVar(argument[1][0][1])

    result = int(argument[1][1][1]) * int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

def idiv(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if (argument[1][0][0]) != 'var':
        sys.exit(32)

    if (argument[1][1][0] != 'int') and (argument[1][2][0] != 'int'):
        sys.exit(53)

    destPrefix, destSuffix = editVar(argument[1][0][1])

    if int(argument[1][2][1]) == 0:
        sys.exit(57)
    result = int(argument[1][1][1]) // int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

def main():
    global hashTable
    sourceFile, inputFile = arg_handler()
    instr = readSource(sourceFile)
    hashTable["GF"] = {}
    order = 0

    while order < len(instr):
        mySwitch(instr[order])
        order += 1


if __name__ == "__main__":
    main()
