"""
Project: Interpret of XML code representation
Author: David Oravec (xorave05)
File: interpret.py
Description:
    Loads XML code, transfomrs it and executes code IPPcode20 which is based on python
"""

import xml.etree.ElementTree as ET
import argparse
import sys

# GLOBAL variables
hashTable = {}
stackOfFrames = list()
stackOfVars = list()
stackOfCalls = list()
instrPointer, varCounter, instrCounter = 0, 0, 0
statsFile = None

"""
    function for handling arguments
    returns sourceFile (if defined), inputFile (if defined), 
    statsFile (if defined) or exits with proper exit code
"""
def arg_handler():
    argsparser = argparse.ArgumentParser(description="Loads XML code, transforms it to IPPcode20 and executes it")
    argsparser.add_argument("--source", nargs=1, help="Input file with XML code")
    argsparser.add_argument("--input", nargs=1, help="File with inputs(f.e. instruction READ)")
    argsparser.add_argument("--stats", nargs=1, help="Specifies file where wtats will be written")
    argsparser.add_argument("--insts", action="store_true", help="Number of executed instructions, requires --stats")
    argsparser.add_argument("--vars", action="store_true", help="Number of maximum initialized vars, requires --stats")

    args = argsparser.parse_args()
    # there has to be at least one of them defined
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
    global statsFile
    try:
        if args.stats is not None:
            statsFile = open(args.stats[0], "w")
    except:
        sys.exit(12)

    if (args.insts is True or args.vars is True) and statsFile is None:
        sys.exit(10)

    return sourceFile, inputFile, statsFile


"""
   function for parsing source XML file
   returns dict of instruction which contains:
   order, instruction, params
"""
def readSource(sourceFile):
    dictOfIntructions = dict()
    okCheck = False
    try:
        tree = ET.parse(sourceFile).getroot()
    except:
        sys.exit(32)

    opt = ['language', 'name', 'description']
    for attrib, item in tree.attrib.items():
        if attrib == "language" and item == "IPPcode20":
            okCheck = True
        else:
            sys.exit(32)
        if attrib not in opt:
            sys.exit(32)
    if okCheck is False:
        sys.exit(32)

    for instruction in tree:
        if len(instruction.attrib) != 2:
            sys.exit(32)
        order = instruction.attrib["order"]
        opcode = instruction.attrib["opcode"]

        if opcode == "none" or order is None:
            sys.exit(32)

        array = ["\n", " ", "\t", "\v", "\f", "\r", "#"]    # these are forbidden
        types = ["string", "int", "var", "type", "nil", "bool", "label", "float"]
        instructions = dict()
        instructions[int(order)] = list()
        args = list()
        try:
            for i in range(len(instruction)):
                xmlArg = instruction.find("arg" + str(i + 1))
                if xmlArg.attrib["type"] not in types:
                    exit(53)
                if len(xmlArg.attrib) != 1:
                    sys.exit(32)
                if xmlArg.attrib["type"] == 'string' and xmlArg.text is not None:
                    if any(idx in xmlArg.text for idx in array):
                        sys.exit(32)
                    xmlArg.text = changeString(xmlArg.text)
                if xmlArg.attrib["type"] == 'string' and xmlArg.text is None:
                    arg = ('string', "")
                else:
                    arg = (xmlArg.attrib["type"], xmlArg.text)
                args.append(arg)
                if xmlArg.tail and xmlArg.tail.strip() != "":
                    raise
        except:
            sys.exit(31)
        instructions[int(order)].append(opcode)
        instructions[int(order)].append(args)
        dictOfIntructions.update(instructions)
        if (instruction.tail and instruction.tail.strip() != "") or\
                (instruction.text and instruction.text.strip() != ""):
            sys.exit(31)
    dictOfIntructions = sorted(dictOfIntructions.items(), key=lambda x: x[0])
    for order, val in dictOfIntructions:
        if order < 0:
            sys.exit(32)
    if (tree.tail and tree.tail.strip() != "") or \
            (tree.text and tree.text.strip() != ""):
        sys.exit(31)

    return dictOfIntructions


"""
    returns True if var is valid operand, otherwise False
"""
def checkSymb(var):
    if var == 'string' or var == 'int' or var == 'bool' or var == 'nil'\
            or var == 'float':
        return True
    else:
        return False


"""
    edit var and returns prefix and sufix to hashTable
"""
def editVar(var):
    if var.find("@") == -1:
        sys.exit(32)
    else:
        prefix = var[:2]
        suffix = var[3:]

    return prefix, suffix


"""
    removes escape sequences from strings
"""
def changeString(str):
    for index, change in enumerate(str.split("\\")):
        if index == 0:
            str = change
        else:
            str = str + chr(int(change[0:3])) + change[3:]
    return str


"""
    checks if operand is correct
"""
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


"""
    looks if prefix and suffix are initialized in hashTable
"""
def inTable(pref, suf):
    if pref not in hashTable:
        return 55
    if suf not in hashTable[pref]:
        return 54
    return 0


"""
    gets value from var which is in hashTable
"""
def fromTable(arg):
    pref, suf = editVar(arg)
    code = inTable(pref, suf)
    if code != 0:
        sys.exit(code)

    result = hashTable[pref][suf]
    if result is None:
        sys.exit(56)
    return result


"""
    function which imitates switch like in C
"""
def mySwitch(argument):
    switcher = {"MOVE": move,
                "CREATEFRAME": createframe,
                "PUSHFRAME": pushframe,
                "POPFRAME": popframe,
                "DEFVAR": defvar,
                "CALL": call,
                "RETURN": returnInstr,
                "PUSHS": pushs,
                "POPS": pops,
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
                "SETCHAR": setchar,
                "TYPE": typeInstr,
                "EXIT": exitInstr,
                "LABEL": label,
                "DPRINT": dprint,
                "JUMP": jump,
                "JUMPIFEQ": jumpifeq,
                "JUMPIFNEQ": jumpifneq,
                "BREAK": breakInstr,
                "ADDS": adds,
                "SUBS": subs,
                "MULS": muls,
                "IDIVS": idivs,
                "LTS": lts,
                "GTS": gts,
                "EQS": eqs,
                "ANDS": ands,
                "ORS": ors,
                "NOTS": nots,
                "INT2CHARS": int2chars,
                "STRI2INTS": stri2ints,
                "JUMPIFEQS": jumpifeqs,
                "JUMPIFNEQS": jumpifneqs,
                "CLEARS": clears,
                "DIV": div,
                "INT2FLOAT": int2float,
                "FLOAT2INT": float2int,
                "DIVS": divs,
                "INT2FLOATS": int2floats,
                "FLOAT2INTS": float2ints}
    execs = switcher.get(argument[1][0], lambda: "Wrong instruction!\n")
    return execs(argument[1])


# MOVE ⟨var⟩ ⟨symb⟩
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


# CREATEFRAME
def createframe(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)
    hashTable["TF"] = {}


# PUSHFRAME
def pushframe(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)
    if "TF" not in hashTable:
        sys.exit(55)
    if "LF" in hashTable:
        stackOfFrames.append(hashTable["LF"])  # appending frame to stack
    hashTable["LF"] = hashTable.pop("TF")  # frame TF is replaced by LF


# POPFRAME
def popframe(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)
    if "LF" not in hashTable:
        sys.exit(55)
    hashTable["TF"] = hashTable.pop("LF")
    if len(stackOfFrames) >= 1:
        hashTable["LF"] = stackOfFrames.pop()


# DEFVAR ⟨var⟩
def defvar(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)

    if (argument[1][0][0]) != 'var':
        sys.exit(32)
    pref, suf = editVar(argument[1][0][1])
    if pref not in hashTable:
        sys.exit(55)
    if suf in hashTable[pref]:
        sys.exit(52)
    else:
        hashTable[pref][suf] = None


# CALL ⟨label⟩
def call(argument):
    global instrPointer
    if (len(argument[1])) != 1:
        sys.exit(32)

    if argument[1][0][0] != 'label':
        sys.exit(32)

    if argument[1][0][1] not in hashTable["label"]:
        sys.exit(52)

    stackOfCalls.append(instrPointer + 1)
    instrPointer = hashTable["label"][argument[1][0][1]]


# RETURN
def returnInstr(argument):
    global instrPointer
    if len(argument[1]) > 0:
        sys.exit(32)

    if len(stackOfCalls) != 0:
        instrPointer = stackOfCalls.pop()
    else:
        sys.exit(56)


# ADD ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def add(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if argument[1][1][0] == 'float' or argument[1][2][0] == 'float':
        exp = 'float'
    else:
        exp = 'int'
    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    try:
        if exp == 'float':
            result = float(float.fromhex(argument[1][1][1])) + float(float.fromhex(argument[1][2][1]))
            result = float.hex(result)
            hashTable[destPrefix][destSuffix] = ('float', str(result))
        else:
            result = int(argument[1][1][1]) + int(argument[1][2][1])
            hashTable[destPrefix][destSuffix] = ('int', str(result))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# SUB ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def sub(argument):

    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if argument[1][1][0] == 'float' or argument[1][2][0] == 'float':
        exp = 'float'
    else:
        exp = 'int'

    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)
    try:
        if exp == 'float':
            result = float(float.fromhex(argument[1][1][1])) - float(float.fromhex(argument[1][2][1]))
            result = float.hex(result)
            hashTable[destPrefix][destSuffix] = ('float', str(result))
        else:
            result = int(argument[1][1][1]) - int(argument[1][2][1])
            hashTable[destPrefix][destSuffix] = ('int', str(result))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# MUL ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def mul(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if argument[1][1][0] == 'float' or argument[1][2][0] == 'float':
        exp = 'float'
    else:
        exp = 'int'

    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    try:
        if exp == 'float':
            result = float(float.fromhex(argument[1][1][1])) * float(float.fromhex(argument[1][2][1]))
            result = float.hex(result)
            hashTable[destPrefix][destSuffix] = ('float', str(result))
        else:
            result = int(argument[1][1][1]) * int(argument[1][2][1])
            hashTable[destPrefix][destSuffix] = ('int', str(result))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# IDIV ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def idiv(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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
    try:
        result = int(argument[1][1][1]) // int(argument[1][2][1])
        hashTable[destPrefix][destSuffix] = ('int', str(result))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# DIV ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def div(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'float'
    code = checkErr(argument[1][0][0], exp, exp, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)
    if float.fromhex(argument[1][2][1]) == 0:
        sys.exit(57)

    try:
        result = float(float.fromhex(argument[1][1][1])) / float(float.fromhex(argument[1][2][1]))
        result = result.hex()
        hashTable[destPrefix][destSuffix] = ('float', str(result))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# LT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def lt(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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

    try:
        if argument[1][1][0] == 'int':
            result = int(argument[1][1][1]) < int(argument[1][2][1])
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
        elif argument[1][1][0] == 'string':
            result = argument[1][1][1] < argument[1][2][1]
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
        elif argument[1][1][0] == 'bool':
            if argument[1][1][1] == 'false' and argument[1][2][1] == 'true':
                hashTable[destPrefix][destSuffix] = ('bool', 'true')
            else:
                hashTable[destPrefix][destSuffix] = ('bool', 'false')
        elif argument[1][1][0] == 'float':
            result = float(float.fromhex(argument[1][1][1])) < float(float.fromhex(argument[1][2][1]))
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# GT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def gt(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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

    try:
        if argument[1][1][0] == 'int':
            result = int(argument[1][1][1]) > int(argument[1][2][1])
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
        elif argument[1][1][0] == 'string':
            result = argument[1][1][1] > argument[1][2][1]
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
        elif argument[1][1][0] == 'bool':
            if argument[1][1][1] == 'true' and argument[1][2][1] == 'false':
                hashTable[destPrefix][destSuffix] = ('bool', 'true')
            else:
                hashTable[destPrefix][destSuffix] = ('bool', 'false')
        elif argument[1][1][0] == 'float':
            result = float(float.fromhex(argument[1][1][1])) > float(float.fromhex(argument[1][2][1]))
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# EQ ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def eq(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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
            hashTable[destPrefix][destSuffix] = ('bool', 'true')
        else:
            hashTable[destPrefix][destSuffix] = ('bool', 'false')
        return

    if argument[1][1][0] != argument[1][2][0]:
        sys.exit(53)

    try:
        if argument[1][1][0] == 'int':
            result = int(argument[1][1][1]) == int(argument[1][2][1])
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
        elif argument[1][1][0] == 'string':
            result = argument[1][1][1] == argument[1][2][1]
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
        elif argument[1][1][0] == 'bool':
            if argument[1][1][1] == 'true' and argument[1][2][1] == 'true' or \
                    argument[1][1][1] == 'false' and argument[1][2][1] == 'false':
                hashTable[destPrefix][destSuffix] = ('bool', 'true')
            else:
                hashTable[destPrefix][destSuffix] = ('bool', 'false')
        elif argument[1][1][0] == 'float':
            result = float(float.fromhex(argument[1][1][1])) == float(float.fromhex(argument[1][2][1]))
            hashTable[destPrefix][destSuffix] = ('bool', str(result).lower())
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# AND ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def andInstr(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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
        hashTable[destPrefix][destSuffix] = ('bool', 'true')
    else:
        hashTable[destPrefix][destSuffix] = ('bool', 'false')

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# OR ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def orInstr(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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

    if argument[1][1][1] == 'true' or argument[1][2][1] == 'true':
        hashTable[destPrefix][destSuffix] = ('bool', 'true')
    else:
        hashTable[destPrefix][destSuffix] = ('bool', 'false')

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# NOT ⟨var⟩ ⟨symb1⟩
def notInstr(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    tempArg1 = argument[1][1]

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
        hashTable[destPrefix][destSuffix] = ('bool', 'false')
    else:
        hashTable[destPrefix][destSuffix] = ('bool', 'true')

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1


# INT2CHAR ⟨var⟩ ⟨symb1⟩
def int2char(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    tempArg1 = argument[1][1]

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

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1


# STRI2INT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def stri2int(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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
    try:
        word = argument[1][1][1]
        index = int(argument[1][2][1])
    except:
        sys.exit(32)

    if int(index) < 0:
        sys.exit(58)

    try:
        result = word[int(index)]
        hashTable[destPrefix][destSuffix] = ('int', ord(result))
    except:
        sys.exit(58)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# INT2FLOAT ⟨var⟩ ⟨symb⟩
def int2float(argument):
    if len(argument[1]) != 2:
        sys.exit(32)

    tempArg1 = argument[1][1]

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
        result = float(int(argument[1][1][1])).hex()
        hashTable[destPrefix][destSuffix] = ('float', result)
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1


# FLOAT2INT ⟨var⟩ ⟨symb⟩
def float2int(argument):
    if len(argument[1]) != 2:
        sys.exit(32)

    tempArg1 = argument[1][1]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var

    exp = 'float'
    exp2 = None
    code = checkErr(argument[1][0][0], exp, exp2, argument[1][1][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    try:
        result = float.fromhex(argument[1][1][1])
        hashTable[destPrefix][destSuffix] = ('int', int(result))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1


# READ ⟨var⟩ ⟨type⟩
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

    if type == 'int' or type == 'string' or type == 'bool' or type == 'float':
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
                hashTable[destPrefix][destSuffix] = ('nil', 'nil')
            else:
                if str(result).lower() != 'true':
                    hashTable[destPrefix][destSuffix] = ('bool', 'false')
                else:
                    hashTable[destPrefix][destSuffix] = ('bool', 'true')
        elif type == 'float':
            if result == "":
                hashTable[destPrefix][destSuffix] = ('nil', 'nil')
            else:
                try:
                    hashTable[destPrefix][destSuffix] = ('float', str(float.fromhex(result).hex()))
                except:
                    hashTable[destPrefix][destSuffix] = ('nil', 'nil')
    else:
        sys.exit(57)


# WRITE ⟨symb⟩
def write(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)

    tempArg1 = argument[1][0]

    if argument[1][0][0] == 'var':
        var = fromTable(argument[1][0][1])
        argument[1][0] = var

    if checkSymb(argument[1][0][0]) is False:
        sys.exit(53)

    if argument[1][0][0] == 'nil':
        print("", end='')
    else:
        if argument[1][0][0] == 'float':
            try:
                print(str(float.fromhex(argument[1][0][1]).hex()), end='')
            except:
                print(float(argument[1][0][1]).hex(), end='')
        else:
            print(argument[1][0][1], end='')

    if tempArg1 != argument[1][0]:
        argument[1][0] = tempArg1


# CONCAT ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def concat(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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

    try:
        hashTable[destPrefix][destSuffix] = ('string', str(argument[1][1][1] + argument[1][2][1]))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# STRLEN ⟨var⟩ ⟨symb1⟩
def strlen(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    tempArg1 = argument[1][1]

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

    try:
        hashTable[destPrefix][destSuffix] = ('int', int(len(argument[1][1][1])))
    except:
        sys.exit(32)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1


# GETCHAR ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def getchar(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

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

    try:
        word = argument[1][1][1]
        index = int(argument[1][2][1])
    except:
        sys.exit(32)

    if int(index) < 0 or int(index) > len(word) - 1:
        sys.exit(58)

    hashTable[destPrefix][destSuffix] = ('string', str(word[int(index)]))

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# SETCHAR ⟨var⟩ ⟨symb1⟩ ⟨symb2⟩
def setchar(argument):
    if (len(argument[1])) != 3:
        sys.exit(32)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    exp = 'int'
    exp2 = 'string'
    code = checkErr(argument[1][0][0], exp, exp2, argument[1][1][0], argument[1][2][0])
    if code != 0:
        sys.exit(code)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    word = fromTable(argument[1][0][1])
    if word[0] != 'string':
        sys.exit(53)
    try:
        index = int(argument[1][1][1])
        char = argument[1][2][1]
    except:
        sys.exit(32)

    if char == "":
        sys.exit(58)
    if int(index) < 0 or int(index) > len(word[1]) - 1:
        sys.exit(58)

    result = word[1]
    result = result[:index] + char[0:1] + result[index + 1:]

    hashTable[destPrefix][destSuffix] = ('string', str(result))

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# TYPE ⟨var⟩ ⟨symb⟩
def typeInstr(argument):
    if (len(argument[1])) != 2:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(32)

    destPrefix, destSuffix = editVar(argument[1][0][1])
    code = inTable(destPrefix, destSuffix)
    if code != 0:
        sys.exit(code)

    if argument[1][1][0] == 'var':
        pref, suf = editVar(argument[1][1][1])
        code = inTable(pref, suf)
        if code != 0:
            sys.exit(code)
        result = hashTable[pref][suf]
        if result is None:
            result = ""
        else:
            result = result[0]
    else:
        if checkSymb(argument[1][1][0]) is False:
            sys.exit(53)
        else:
            result = argument[1][1][0]

    hashTable[destPrefix][destSuffix] = ('string', str(result))


# EXIT ⟨symb⟩
def exitInstr(argument):
    global statsFile
    if (len(argument[1])) != 1:
        sys.exit(32)

    if argument[1][0][0] == 'var':
        var = fromTable(argument[1][0][1])
        argument[1][0] = var

    if argument[1][0][0] != 'int':
        sys.exit(53)

    if 0 <= int(argument[1][0][1]) <= 49:
        # if stats are included we have to write it out
        if statsFile is not None:
            for argv in sys.argv:
                if argv == '--insts':
                    statsFile.write(str(instrCounter) + '\n')
                if argv == '--vars':
                    statsFile.write(str(varCounter) + '\n')
            statsFile.close()
        sys.exit(int(argument[1][0][1]))
    else:
        sys.exit(57)


# this functions creates label before the interpretation of code
# LABEL ⟨label⟩
def createLabel(argument):
    global instrPointer
    if (len(argument[1][1])) != 1:
        sys.exit(32)

    if argument[1][1][0][0] != 'label':
        sys.exit(32)

    if argument[1][1][0][1] in hashTable["label"]:
        sys.exit(52)
    hashTable["label"][argument[1][1][0][1]] = argument[0] - 1


# pass because of createLabel
def label(argument):
    pass


# JUMP ⟨label⟩
def jump(argument):
    global instrPointer
    if len(argument[1]) != 1:
        sys.exit(32)

    if argument[1][0][0] != 'label':
        sys.exit(53)

    if argument[1][0][1] not in hashTable["label"]:
        sys.exit(52)

    instrPointer = hashTable["label"][argument[1][0][1]]


# JUMPIFEQ ⟨label⟩ ⟨symb1⟩ ⟨symb2⟩
def jumpifeq(argument):
    global instrPointer
    if len(argument[1]) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'label':
        sys.exit(53)

    if argument[1][0][1] not in hashTable["label"]:
        sys.exit(52)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if str(argument[1][1][0]) == str(argument[1][2][0]):
        if str(argument[1][1][1]) == str(argument[1][2][1]):
            instrPointer = hashTable["label"][argument[1][0][1]]
    elif str(argument[1][1][0]) == 'nil' or str(argument[1][2][0]) == 'nil':
        if str(argument[1][1][0]) == 'nil' and str(argument[1][2][0]) == 'nil':
            if str(argument[1][1][1]) == 'nil' and str(argument[1][2][1]) == 'nil':
                instrPointer = hashTable["label"][argument[1][0][1]]
    else:
        sys.exit(53)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# JUMPIFNEQ ⟨label⟩ ⟨symb1⟩ ⟨symb2⟩
def jumpifneq(argument):
    global instrPointer
    if len(argument[1]) != 3:
        sys.exit(32)

    if argument[1][0][0] != 'label':
        sys.exit(53)

    if argument[1][0][1] not in hashTable["label"]:
        sys.exit(52)

    tempArg1 = argument[1][1]
    tempArg2 = argument[1][2]

    if argument[1][1][0] == 'var':
        var = fromTable(argument[1][1][1])
        argument[1][1] = var
    if argument[1][2][0] == 'var':
        var = fromTable(argument[1][2][1])
        argument[1][2] = var

    if str(argument[1][1][0]) == str(argument[1][2][0]):
        if argument[1][1][1] != argument[1][2][1]:
            instrPointer = hashTable["label"][argument[1][0][1]]
    elif str(argument[1][1][0]) == 'nil' or str(argument[1][2][0]) == 'nil':
        if str(argument[1][1][0]) == 'nil' and str(argument[1][2][0]) == 'nil':
            if str(argument[1][1][1]) == "" and str(argument[1][2][1]) == "":
                pass
            else:
                instrPointer = hashTable["label"][argument[1][0][1]]
        else:
            instrPointer = hashTable["label"][argument[1][0][1]]
    else:
        sys.exit(53)

    if tempArg1 != argument[1][1]:
        argument[1][1] = tempArg1
    if tempArg2 != argument[1][2]:
        argument[1][2] = tempArg2


# DPRINT ⟨symb⟩
def dprint(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)

    tempArg1 = argument[1][0]

    if argument[1][0][0] == 'var':
        var = fromTable(argument[1][0][1])
        argument[1][0] = var

    sys.stderr.write(str(argument[1][0][1]))

    if tempArg1 != argument[1][0]:
        argument[1][0] = tempArg1


# PUSHS ⟨symb⟩
def pushs(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)

    tempArg1 = argument[1][0]

    if argument[1][0][0] == 'var':
        pref, suf = editVar(argument[1][0][1])
        code = inTable(pref, suf)
        if code != 0:
            sys.exit(code)
        var = fromTable(argument[1][0][1])
        argument[1][0] = var

    if checkSymb(argument[1][0][0]) is False:
        sys.exit(53)

    stackOfVars.append((argument[1][0][0], argument[1][0][1]))

    if tempArg1 != argument[1][0]:
        argument[1][0] = tempArg1


# POPS ⟨var⟩
def pops(argument):
    if (len(argument[1])) != 1:
        sys.exit(32)

    if argument[1][0][0] != 'var':
        sys.exit(53)

    destPref, destSuf = editVar(argument[1][0][1])
    code = inTable(destPref, destSuf)
    if code != 0:
        sys.exit(code)

    if len(stackOfVars) != 0:
        hashTable[destPref][destSuf] = stackOfVars.pop()
    else:
        sys.exit(56)


# BREAK
def breakInstr(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    sys.stderr.write("Code is now processing instruction: " + str(instrPointer + 1) + '\n' +
                     "Content in Global Frame: " + str(hashTable["GF"]) + '\n' +
                     "Names of the defined labels and its index: " + str(hashTable["label"]) + '\n')
    try:
        if "TF" in hashTable:
            sys.stderr.write("Content in Temporary Frame: " + str(hashTable["TF"]) + '\n')
        if "LF" in hashTable:
            sys.stderr.write("Content in Local Frame: " + str(hashTable["LF"]) + '\n')
    except:
        pass


############################################################################
#                           ROZSIRENIE STACK                               #
############################################################################


def adds(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if (var2[0] != 'int' or var1[0] != 'int') and \
            (var2[0] != 'float' or var1[0] != 'float'):
        sys.exit(53)

    try:
        if var1[0] == 'int':
            result = int(var1[1]) + int(var2[1])
            stackOfVars.append(('int', str(result)))
        else:
            result = float(float.fromhex(var1[1]) + float(float.fromhex(var2[1])))
            result = float.hex(result)
            stackOfVars.append(('float', str(result)))
    except:
        sys.exit(32)


def subs(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if (var2[0] != 'int' or var1[0] != 'int') and \
            (var2[0] != 'float' or var1[0] != 'float'):
        sys.exit(53)

    try:
        if var1[0] == 'int':
            result = int(var1[1]) - int(var2[1])
            stackOfVars.append(('int', str(result)))
        else:
            result = float(float.fromhex(var1[1]) - float(float.fromhex(var2[1])))
            result = float.hex(result)
            stackOfVars.append(('float', str(result)))
    except:
        sys.exit(32)


def muls(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if (var2[0] != 'int' or var1[0] != 'int') and \
            (var2[0] != 'float' or var1[0] != 'float'):
        sys.exit(53)

    try:
        if var1[0] == 'int':
            result = int(var1[1]) * int(var2[1])
            stackOfVars.append(('int', str(result)))
        else:
            result = float(float.fromhex(var1[1]) * float(float.fromhex(var2[1])))
            result = float.hex(result)
            stackOfVars.append(('float', str(result)))
    except:
        sys.exit(32)


def idivs(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var2[0] != 'int' or var1[0] != 'int':
        sys.exit(53)

    if int(var2[1]) == 0:
        sys.exit(57)

    try:
        result = int(var1[1]) // int(var2[1])
        stackOfVars.append(('int', str(result)))
    except:
        sys.exit(32)


def divs(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var2[0] != 'float' or var1[0] != 'float':
        sys.exit(53)

    if float.fromhex(var2[1]) == 0:
        sys.exit(57)

    try:
        result = float(float.fromhex(var1[1])) / float(float.fromhex(var2[1]))
        result = result.hex()
        stackOfVars.append(('float', str(result)))
    except:
        sys.exit(32)


def lts(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != var2[0]:
        sys.exit(53)

    if var1[0] == 'nil' or var2[0] == 'nil':
        sys.exit(53)

    try:
        if var1[0] == 'int' and var2[0] == 'int':
            result = int(var1[1]) < int(var2[1])
            stackOfVars.append(('bool', str(result).lower()))
        elif var1[0] == 'string' and var2[0] == 'string':
            result = str(var1[1]) < str(var2[1])
            stackOfVars.append(('bool', str(result).lower()))
        elif var1[0] == 'bool' and var2[0] == 'bool':
            if var1[1] == 'false' and var2[1] == 'true':
                stackOfVars.append(('bool', 'true'))
            else:
                stackOfVars.append(('bool', 'false'))
        elif var1[0] == 'float' and var2[0] == 'float':
            result = float(float.fromhex(var1[1])) < float(float.fromhex(var2[1]))
            stackOfVars.append(('bool', str(result).lower()))
    except:
        sys.exit(32)


def gts(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != var2[0]:
        sys.exit(53)

    if var1[0] == 'nil' or var2[0] == 'nil':
        sys.exit(53)

    try:
        if var1[0] == 'int' and var2[0] == 'int':
            result = int(var1[1]) > int(var2[1])
            stackOfVars.append(('bool', str(result).lower()))
        elif var1[0] == 'string' and var2[0] == 'string':
            result = str(var1[1]) > str(var2[1])
            stackOfVars.append(('bool', str(result).lower()))
        elif var1[0] == 'bool' and var2[0] == 'bool':
            if var1[1] == 'true' and var2[1] == 'false':
                stackOfVars.append(('bool', 'true'))
            else:
                stackOfVars.append(('bool', 'false'))
        elif var1[0] == 'float' and var2[0] == 'float':
            result = float(float.fromhex(var1[1])) > float(float.fromhex(var2[1]))
            stackOfVars.append(('bool', str(result).lower()))
    except:
        sys.exit(32)


def eqs(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] == 'nil' or var2[0] == 'nil':
        if var1[1] == 'nil' and var2[1] == 'nil':
            stackOfVars.append(('bool', 'true'))
        else:
            stackOfVars.append(('bool', 'false'))
        return

    if var1[0] != var2[0]:
        sys.exit(53)
    try:
        if var1[0] == 'int' and var2[0] == 'int':
            result = int(var1[1]) == int(var2[1])
            stackOfVars.append(('bool', str(result).lower()))
        elif var1[0] == 'string' and var2[0] == 'string':
            result = str(var1[1]) == str(var2[1])
            stackOfVars.append(('bool', str(result).lower()))
        elif var1[0] == 'bool' and var2[0] == 'bool':
            if var1[1] == var2[1]:
                stackOfVars.append(('bool', 'true'))
            else:
                stackOfVars.append(('bool', 'false'))
        elif var1[0] == 'float' and var2[0] == 'float':
            result = float(float.fromhex(var1[1])) == float(float.fromhex(var2[1]))
            stackOfVars.append(('bool', str(result).lower()))
    except:
        sys.exit(32)


def ands(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != 'bool' or var2[0] != 'bool':
        sys.exit(53)

    if var1[1] == 'true' and var2[1] == 'true':
        stackOfVars.append(('bool', 'true'))
    else:
        stackOfVars.append(('bool', 'false'))


def ors(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != 'bool' or var2[0] != 'bool':
        sys.exit(53)

    if var1[1] == 'true' or var2[1] == 'true':
        stackOfVars.append(('bool', 'true'))
    else:
        stackOfVars.append(('bool', 'false'))


def nots(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != 'bool':
        sys.exit(53)

    if var1[1] == 'true':
        stackOfVars.append(('bool', 'false'))
    else:
        stackOfVars.append(('bool', 'true'))


def int2chars(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != 'int':
        sys.exit(53)

    try:
        stackOfVars.append(('string', chr(int(var1[1]))))
    except:
        sys.exit(58)


def stri2ints(argument):
    if (len(argument[1])) > 0:
        sys.exit(32)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var2[0] != 'int':
        sys.exit(53)

    if var1[0] != 'string':
        sys.exit(53)

    if int(var2[1]) < 0 or int(var2[1]) > len(var1[1]):
        sys.exit(58)

    try:
        result = var1[1][int(var2[1])]
        stackOfVars.append(('int', ord(result)))
    except:
        sys.exit(58)


def int2floats(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    try:
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != 'int':
        sys.exit(53)

    try:
        result = float(int(var1[1])).hex()
        stackOfVars.append(('float', result))
    except:
        sys.exit(32)


def float2ints(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    try:
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] != 'float':
        sys.exit(53)

    try:
        result = float.fromhex(var1[1])
        stackOfVars.append(('int', int(result)))
    except:
        sys.exit(32)


def jumpifeqs(argument):
    global instrPointer
    if (len(argument[1])) != 1:
        sys.exit(32)

    if argument[1][0][0] != 'label':
        sys.exit(32)
    if argument[1][0][1] not in hashTable["label"]:
        sys.exit(52)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] == var2[0]:
        if var1[1] == var2[1]:
            instrPointer = hashTable["label"][argument[1][0][1]]
    elif var1[0] == 'nil' or var2[0] == 'nil':
        if var1[0] == 'nil' and var2[0] == 'nil':
            if var1[1] == 'nil' and var2[1] == 'nil':
                instrPointer = hashTable["label"][argument[1][0][1]]
    else:
        sys.exit(53)


def jumpifneqs(argument):
    global instrPointer
    if (len(argument[1])) != 1:
        sys.exit(32)

    if argument[1][0][0] != 'label':
        sys.exit(32)
    if argument[1][0][1] not in hashTable["label"]:
        sys.exit(52)

    try:
        var2 = stackOfVars.pop()
        var1 = stackOfVars.pop()
    except:
        sys.exit(56)

    if var2[0] == 'var':
        var = fromTable(var2[1])
        var2[0] = var
    if var1[0] == 'var':
        var = fromTable(var1[1])
        var1[0] = var

    if var1[0] == var2[0]:
        if var1[1] != var2[1]:
            instrPointer = hashTable["label"][argument[1][0][1]]
    elif var1[0] == 'nil' or var2[0] == 'nil':
        if var1[0] == 'nil' and var2[0] == 'nil':
            if var1[1] == 'nil' and var2[1] == 'nil':
                pass
            else:
                instrPointer = hashTable["label"][argument[1][0][1]]
        else:
            instrPointer = hashTable["label"][argument[1][0][1]]
    else:
        sys.exit(53)


def clears(argument):
    if len(argument[1]) > 0:
        sys.exit(32)

    for i in range(0, len(stackOfVars)):
        stackOfVars.pop()


def main():
    global hashTable
    global instrPointer
    global instrCounter
    global varCounter
    sourceFile, inputFile, statsFile = arg_handler()
    sys.stdin = inputFile
    instr = readSource(sourceFile)
    hashTable["GF"] = {}
    hashTable["label"] = {}
    for i in range(0, len(instr)):
        if instr[i][1][0] == 'LABEL':
            createLabel(instr[i])

    while instrPointer < len(instr):
        flag = False
        if instr[instrPointer][1][0] == 'RETURN':
            flag = True
        if statsFile is not None:
            instrCounter += 1
        mySwitch(instr[instrPointer])

        if flag:
            pass
        else:
            instrPointer += 1

        if statsFile is not None:
            counter = 0
            for var in hashTable["GF"]:
                if var is not None:
                    counter += 1
            if "LF" in hashTable:
                if hashTable["LF"] is not None:
                    for var in hashTable["LF"]:
                        if var is not None:
                            counter += 1
            if "TF" in hashTable:
                if hashTable["TF"] is not None:
                    for var in hashTable["TF"]:
                        if var is not None:
                            counter += 1
            varCounter = max(varCounter, counter)

    if statsFile is not None:
        for argv in sys.argv:
            if argv == '--insts':
                statsFile.write(str(instrCounter) + '\n')
            if argv == '--vars':
                statsFile.write(str(varCounter) + '\n')
        statsFile.close()


if __name__ == "__main__":
    main()
