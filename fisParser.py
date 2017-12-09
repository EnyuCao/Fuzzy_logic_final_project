#!/usr/bin/env python3
import sys
import os.path
from FLS import TriangularMF, TrapezoidalMF, GaussianMF, BellShapedMF, SigmoidalMF
from FLS import Variable, Input, Output, Rule, Rulebase
import re


def parseMF(line):
    """ Returns a membership function based on the given fis line """
    # l[1] = name
    # l[2] = mf type
    # l[3] = mf args

    l = line.replace("'", '').replace(':', '=').replace(',', '=')
    l = l.split('=')
    args = l[3].strip().replace('[', '').replace(']', '').split(' ')

    if l[2] == 'trimf':
        mf = TriangularMF(l[1], int(args[0]), int(args[1]), int(args[2]))

    elif l[2] == 'tramf':
        mf = TrapezoidalMF(l[1], int(args[0]), int(args[1]), int(args[2]), int(args[3]))

    elif l[2] == 'gaumf':
        mf = GaussianMF(l[1], int(args[0]), int(args[1]))

    elif l[2] == 'belmf':
        mf = GaussianMF(l[1], int(args[0]), int(args[1]), int(args[2]))

    elif l[2] == 'sigmf':
        mf = GaussianMF(l[1], int(args[0]), int(args[1]))

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

    r = [l for l in lines if re.match(rangePattern, l)][0]
    r = r.replace("[", '').replace("]", '').split('=')[1].split(' ')

    mfs = []
    for l in [line for line in lines if re.match(mfPattern, line)]:
        mfs.append(parseMF(l))

    if lines[0][1] == 'I':
        return Input(name, (int(r[0]), int(r[1])), mfs)
    else:
        return Output(name, (int(r[0]), int(r[1])), mfs)


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


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Give fis file as argument")
        sys.exit(0)

    filename = sys.argv[1]

    try:
        os.path.isfile(filename)
    except:
        print("File: \'%s\' not found" % filename)
        sys.exit(0)

    f = open(filename).read()

    inputs, outputs = parseInOutput(f)

    rules = [
        Rule({"income":"low", "quality":"amazing"}, ("and", "min"), {"money":"low"}),
        Rule({"income":"medium", "quality":"amazing"}, ("and", "min"), {"money":"low"}),
        Rule({"income":"high", "quality":"amazing"}, ("and", "min"), {"money":"low"}),
        Rule({"income":"low", "quality":"okay"}, ("and", "min"), {"money":"low"}),
        Rule({"income":"medium", "quality":"okay"}, ("and", "min"), {"money":"medium"}),
        Rule({"income":"high", "quality":"okay"}, ("and", "min"), {"money":"medium"}),
        Rule({"income":"low", "quality":"bad"}, ("and", "min"), {"money":"low"}),
        Rule({"income":"medium", "quality":"bad"}, ("and", "min"), {"money":"medium"}),
        Rule({"income":"high", "quality":"bad"}, ("and", "min"), {"money":"high"})
    ]
    rulebase = Rulebase(rules)
    # Test your implementation of calculate_firing_strengths()
    # Enter your answers in the Google form to check them, round to two decimals
    datapoint = {"income":500, "quality":3}
    print(rulebase.get_fs(datapoint, inputs))
    datapoint = {"income":234, "quality":7.5}
    print(rulebase.get_fs(datapoint, inputs))
