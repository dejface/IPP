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

def checkErr(var, expected1, expected2, *symb):
    if var != 'var':
        return 32

    if expected2 is None:
        if symb[0] != expected1:
            return 53
    else:
        if symb[0] != expected1:
            return 53

        if symb[1] != expected2:
            return 53
    return 0

def inTable(pref, suf):

    if pref not in hashTable:
        return 55
    if suf not in hashTable[pref]:
        return 54
    return 0

def fromTable(arg):
    pref, suf = editVar(arg)
    code = inTable(pref, suf)
    if code != 0:
        sys.exit(code)

    result = hashTable[pref][suf]
    if result is None:
        sys.exit(56)
    return result

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
              "IDIV": idiv,
              "LT": lt,
              "GT": gt,
              "EQ": eq,
              "AND": andInstr,
              "OR": orInstr,
              "NOT": notInstr,
              "INT2CHAR": int2char,
              "STRI2INT": stri2int,
              "READ": read,
              "WRITE": write,
              "CONCAT": concat,
              "STRLEN": strlen,
              "GETCHAR": getchar,
              "SETCHAR": setchar}
    execs = switcher.get(argument[1][0], lambda: "Wrong instruction!\n")
    return execs(argument[1])


def move(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    if (argument[1][0][0]) != 'var':
        sys.exit(32)

    if argument[1][1][0] != 'var':
        if checkSymb(argument[1][1][0]) is False:
            sys.exit(32)
        else:
            if argument[1][1][1] is None:
                argument[1][1][1] = ""
                var = (argument[1][1][0], argument[1][1][1])
            else:
                var = (argument[1][1][0], argument[1][1][1])
    else:
        var = fromTable(argument[1][1][1])

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    hashTable[destPrefix][destSuffix] = var

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
    pref, suf = editVar(argument[1][0][1])
    if pref not in hashTable:
        sys.exit(55)
    hashTable[pref][suf] = None


def call(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)
    pass
    #var = argument[1]

    #hashTable["label"][var]
    #TODO

# GLOBAL TODO treba osetrit: -ci je premenna definovana v tabulke symbolov, kontrola
#                            -pokial je argument v premennej, tak ziskat jeho content

# ADD ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def add(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'int'
    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    result = int(argument[1][1][1]) + int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

# SUB ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def sub(argument):
    # TODO aj v add overit definovanost v tabulke a ak by nebol type int ale var
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'int'
    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    result = int(argument[1][1][1]) - int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

# MUL ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def mul(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'int'
    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    result = int(argument[1][1][1]) * int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

# IDIV ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def idiv(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'int'
    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if int(argument[1][2][1]) == 0:
        sys.exit(57)
    result = int(argument[1][1][1]) // int(argument[1][2][1])

    hashTable[destPrefix][destSuffix] = ("int", str(result))

# LT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def lt(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if (checkSymb(argument[1][1][0]) or checkSymb(argument[1][2][0])) is False:
        sys.exit(53)

    if argument[1][1][0] == 'nil' or argument[1][2][0] == 'nil':
        sys.exit(53)

    if argument[1][1][0] != argument[1][2][0]:
        sys.exit(53)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if argument[1][1][0] == 'int':
        result = int(argument[1][1][1]) < int(argument[1][2][1])
        hashTable[destPrefix][destSuffix] = ('bool', str(result))
    elif argument[1][1][0] == 'string':
        result = argument[1][1][1] < argument[1][2][1]
        hashTable[destPrefix][destSuffix] = ('bool', result)
    elif argument[1][1][0] == 'bool':
        if argument[1][1][1] == 'false' and argument[1][2][1] == 'true':
            hashTable[destPrefix][destSuffix] = ('bool', 'True')
        else:
            hashTable[destPrefix][destSuffix] = ('bool', 'False')
    else:
        sys.exit(53)

# GT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def gt(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if (checkSymb(argument[1][1][0]) or checkSymb(argument[1][2][0])) is False:
        sys.exit(53)

    if argument[1][1][0] == 'nil' or argument[1][2][0] == 'nil':
        sys.exit(53)

    if argument[1][1][0] != argument[1][2][0]:
        sys.exit(53)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if argument[1][1][0] == 'int':
        result = int(argument[1][1][1]) > int(argument[1][2][1])
        hashTable[destPrefix][destSuffix] = ('bool', str(result))
    elif argument[1][1][0] == 'string':
        result = argument[1][1][1] > argument[1][2][1]
        hashTable[destPrefix][destSuffix] = ('bool', result)
    elif argument[1][1][0] == 'bool':
        if argument[1][1][1] == 'true' and argument[1][2][1] == 'false':
            hashTable[destPrefix][destSuffix] = ('bool', 'True')
        else:
            hashTable[destPrefix][destSuffix] = ('bool', 'False')
    else:
        sys.exit(53)

# EQ ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def eq(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if (checkSymb(argument[1][1][0]) or checkSymb(argument[1][2][0])) is False:
        sys.exit(53)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if argument[1][1][0] == 'nil' or argument[1][2][0] == 'nil':
        if argument[1][1][1] == 'nil' and argument[1][2][1] == 'nil':
            hashTable[destPrefix][destSuffix] = ('bool', 'True')
        else:
            hashTable[destPrefix][destSuffix] = ('bool', 'False')
        return

    if argument[1][1][0] != argument[1][2][0]:
        sys.exit(53)

    if argument[1][1][0] == 'int':
        result = int(argument[1][1][1]) < int(argument[1][2][1])
        hashTable[destPrefix][destSuffix] = ('bool', str(result))
    elif argument[1][1][0] == 'string':
        result = argument[1][1][1] < argument[1][2][1]
        hashTable[destPrefix][destSuffix] = ('bool', result)
    elif argument[1][1][0] == 'bool':
        if argument[1][1][1] == 'false' and argument[1][2][1] == 'true':
            hashTable[destPrefix][destSuffix] = ('bool', 'True')
        else:
            hashTable[destPrefix][destSuffix] = ('bool', 'False')
    else:
        sys.exit(53)

# AND ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def andInstr(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if argument[1][1][0] != 'bool' or argument[1][2][0] != 'bool':
        sys.exit(53)

    if argument[1][1][1] == 'true' and argument[1][2][1] == 'true':
        hashTable[destPrefix][destSuffix] = ('bool', 'True')
    else:
        hashTable[destPrefix][destSuffix] = ('bool', 'False')

# OR ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def orInstr(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if argument[1][1][0] != 'bool' or argument[1][2][0] != 'bool':
        sys.exit(53)

    if argument[1][1][1] == 'true' or argument[1][2][1] != 'true':
        hashTable[destPrefix][destSuffix] = ('bool', 'True')
    else:
        hashTable[destPrefix][destSuffix] = ('bool', 'False')

# NOT ⟨var⟩ ⟨symb1⟩
def notInstr(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if argument[1][1][0] != 'bool':
        sys.exit(53)

    if argument[1][1][1] == 'true':
        hashTable[destPrefix][destSuffix] = ('bool', 'False')
    else:
        hashTable[destPrefix][destSuffix] = ('bool', 'True')

# INT2CHAR ⟨var⟩ ⟨symb1⟩
def int2char(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var

    exp = 'int'
    exp2 = None
    code = checkErr(argument[1][0][0], exp, exp2, argument[1][1][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    try:
        hashTable[destPrefix][destSuffix] = ('string', chr(int(argument[1][1][1])))
    except:
        sys.exit(58)

# STRI2INT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def stri2int(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'string'
    exp2 = 'int'
    code = checkErr(argument[1][0][0], exp, exp2, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    word = argument[1][1][1]
    index = argument[1][2][1]
    if int(index) < 0:
        sys.exit(58)

    try:
        result = word[int(index)]
        hashTable[destPrefix][destSuffix] = ('int', ord(result))
    except:
        sys.exit(58)

def read(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    exp = 'type'
    exp2 = None
    code = checkErr(argument[1][0][0], exp, exp2, argument[1][1][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    type = argument[1][1][1]

    try:
        result = input()
    except:
        result = ""

    if type == 'int' or type == 'string' or type == 'bool':
        if type == 'int':
            if result == "":
                hashTable[destPrefix][destSuffix] = ('nil', 'nil')
            else:
                try:
                    hashTable[destPrefix][destSuffix] = ('int', str(int(result)))
                except:
                    hashTable[destPrefix][destSuffix] = ('nil', 'nil')
        elif type == 'string':
            if result == "":
                hashTable[destPrefix][destSuffix] = ('nil', 'nil')
            else:
                try:
                    hashTable[destPrefix][destSuffix] = ('string', str(result))
                except:
                    hashTable[destPrefix][destSuffix] = ('nil', 'nil')
        elif type == 'bool':
            if result == "":
                hashTable[destPrefix][destSuffix] = ('bool', 'false')
            else:
                if str(result).lower() != 'true':
                    hashTable[destPrefix][destSuffix] = ('bool', 'false')
                else:
                    hashTable[destPrefix][destSuffix] = ('bool', 'true')
    else:
        sys.exit(57)

def write(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)

    if checkSymb(argument[1][0][0]) is False:
        sys.exit(53)

    if argument[1][0][0] == 'nil':
        print("", end='')
    else:
        print(argument[1][0][1], end='')


# CONCAT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def concat(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'string'
    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    hashTable[destPrefix][destSuffix] = ('string', str(argument[1][1][1] + argument[1][2][1]))

# STRLEN ⟨var⟩ ⟨symb1⟩
def strlen(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var

    exp = 'string'
    exp2 = None
    code = checkErr(argument[1][0][0], exp, exp2, argument[1][1][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    hashTable[destPrefix][destSuffix] = ('int', int(len(argument[1][1][1])))

# GETCHAR ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def getchar(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'string'
    exp2 = 'int'
    code = checkErr(argument[1][0][0], exp, exp2, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    word = argument[1][1][1]
    index = argument[1][2][1]
    if int(index) < 0 or int(index) > len(word)-1:
        sys.exit(58)

    hashTable[destPrefix][destSuffix] = ('string', str(word[int(index)]))


def setchar(argument):
    pass


def main():
    global hashTable
    sourceFile, inputFile = arg_handler()
    instr = readSource(sourceFile)
    hashTable["GF"] = {}
    order = 0

    while order < len(instr):
        mySwitch(instr[order])
        order += 1
    print(hashTable)


if __name__ == "__main__":
    main()
