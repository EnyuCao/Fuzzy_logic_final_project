#!/usr/bin/env python3
import sys
import os.path
from FLS import TriangularMF, TrapezoidalMF, GaussianMF, BellShapedMF
from FLS import SigmoidalMF, Input, Output, Rule, Rulebase
import re


def parseMF(line):
    """ Returns a membership function based on the given fis line """
    # l[1] = name
    # l[2] = mf type
    # l[3] = mf args

    l = line.replace("'", '').replace(':', '=').replace(',', '=')
    l = l.split('=')
    args = l[3].strip().replace('[', '').replace(']', '').split(' ')

    # trimf = TriangularMF
    if l[2] == 'trimf':
        mf = TriangularMF(l[1], float(args[0]), float(args[1]), float(args[2]))

    # trapmf = TrapezoidalMF
    elif l[2] == 'trapmf':
        mf = TrapezoidalMF(l[1], float(args[0]), float(args[1]),
                           float(args[2]), float(args[3]))

    # gaumf = GaussianMF
    elif l[2] == 'gaumf':
        mf = GaussianMF(l[1], float(args[0]), float(args[1]))

    # belmlf = BellShapedMF
    elif l[2] == 'belmf':
        mf = BellShapedMF(l[1], float(args[0]), float(args[1]), float(args[2]))

    # sigmf = SigmoidalMF
    elif l[2] == 'sigmf':
        mf = SigmoidalMF(l[1], float(args[0]), float(args[1]))

    else:
        print("Error:")
        print("Membership function not recognise in line:")
        print(line)
        sys.exit(0)

    return mf


def parseVar(block):
    """Returns the variable declared in the block"""
    mfPattern = r'MF(.)*'
    namePattern = r'Name=(.)*'
    rangePattern = r'Range=(.)*'
    lines = block.split('\n')

    name = [l for l in lines if re.match(namePattern, l)][0]
    name = name.replace("'", "").split("=")[1]

    # Select range
    r = [l for l in lines if re.match(rangePattern, l)][0]
    r = r.replace("[", '').replace("]", '').split('=')[1].split(' ')

    mfs = []
    for l in [line for line in lines if re.match(mfPattern, line)]:
        mfs.append(parseMF(l))

    if lines[0][1] == 'I':
        return Input(name, (float(r[0]), float(r[1])), mfs)
    else:
        return Output(name, (float(r[0]), float(r[1])), mfs)


def parseInOutput(f):
    """
    Returns a list of in and output Variables
    The variables are created from the given fis string
    """
    inPat = r'\[Input(.)*\]'
    outPat = r'\[Output(.)*\]'
    f = f.split('\n\n')

    inputs = []
    for block in [b for b in f if re.match(inPat, b)]:
        inputs.append(parseVar(block))

    outputs = []
    for block in [b for b in f if re.match(outPat, b)]:
        outputs.append(parseVar(block))

    return inputs, outputs


def parseRule(l, inputs, outputs, andMeth, orMeth):
    """Returns a rule based on the given line and args"""
    l = l.replace(',', '').replace('(', '').replace(')', '').replace(':', '')
    l = l.replace('  ', ' ').split(' ')

    inDict = {}
    outDict = {}
    # Input of rules
    for i, x in enumerate(l[:len(inputs)]):
        if int(x) == 0:
            continue
        inVar = inputs[i]
        inDict[inVar.name] = inVar.mfs[int(x) - 1].name

    # Output of rules
    for i, x in enumerate(l[len(inputs):len(inputs) + len(outputs)]):
        if int(x) == 0:
            continue
        outVar = outputs[i]
        outDict[outVar.name] = outVar.mfs[int(x) - 1].name

    # 1 is and
    # 2 is or
    if (l[-1] == '1'):
        operation = ('and', andMeth)
    elif (l[-1] == '2'):
        operation = ('or', orMeth)
    else:
        print("suported operation type:")
        print("1 = 'and', 2 = 'or'")
        print("%s not supported" % l[-1])
        sys.exit(0)

    return Rule(inDict, operation, outDict)


def parseRules(f, inputs, outputs, andMeth, orMeth):
    """ Returns a list of rules based on the given params """
    f = f.split('\n\n')
    rulePat = r'\[Rules\]'

    rules = []
    for block in [b for b in f if re.match(rulePat, b)]:
        lines = block.split('\n')
        for l in lines[1:-1]:
            rules.append(parseRule(l, inputs, outputs, andMeth, orMeth))

    return rules


def parseSetting(l, sysDict):
    """ Adds the setting in the line to the sysDict """

    setting = ""
    # and
    if re.match(r'AndMethod(.)*', l):
        val = l.replace("'", '').split('=')[-1]
        setting = ('and', val)

    # or
    elif re.match(r'OrMethod(.)*', l):
        val = l.replace("'", '').split('=')[-1]
        setting = ('or', val)

    # imp
    elif re.match(r'ImpMethod(.)*', l):
        val = l.replace("'", '').split('=')[-1]
        setting = ('imp', val)

    # aggregation
    elif re.match(r'AggMethod(.)*', l):
        val = l.replace("'", '').split('=')[-1]
        setting = ('agg', val)

    # defuzz
    elif re.match(r'DefuzzMethod(.)*', l):
        val = l.replace("'", '').split('=')[-1]
        setting = ('defuzz', val)

    if setting != "":
        sysDict[setting[0]] = setting[1]


def parseSystem(f):
    """ Returns a dict with the system settings """
    f = f.split('\n\n')
    sysPat = r'\[System\]'

    sysDict = {}
    for block in [b for b in f if re.match(sysPat, b)]:
        for l in block.split('\n'):
            parseSetting(l, sysDict)

    return sysDict


def parseFisFile(filename):
    """
    returns inputs outputs rules and setting dict
    taken from the given .fis filename
    """

    try:
        os.path.isfile(filename)
    except:
        print("File: \'%s\' not found" % filename)
        sys.exit(0)

    f = open(filename).read()

    sysDict = parseSystem(f)
    inputs, outputs = parseInOutput(f)
    rules = parseRules(f, inputs, outputs, sysDict['and'], sysDict['or'])
    rulebase = Rulebase(rules)

    return sysDict, inputs, outputs, rulebase


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Give fis file as argument")
        sys.exit(0)

    sysDict, inputs, outputs, rulebase = parseFisFile(sys.argv[1])

    datapoint = {"income": 500, "quality": 3}
    print(rulebase.get_fs(datapoint, inputs))
    datapoint = {"income": 234, "quality": 7.5}
    print(rulebase.get_fs(datapoint, inputs))
