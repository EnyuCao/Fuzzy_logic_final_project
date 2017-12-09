#!/usr/bin/env python3
import sys
import os.path
from FLS import TriangularMF, TrapezoidalMF, GaussianMF, BellShapedMF, SigmoidalMF
from FLS import Variable, Input, Output, Rule, Rulebase
import re


def parseMF(line):
    # l[1] = name
    # l[2] = mf type
    # l[3] = mf args

    line = line.replace("'", '').replace(':', '=').replace(',', '=')
    line = line.split('=')
    args = line[3].strip().replace('[', '').replace(']', '').split(' ')

    # print(line[2])
    if line[2] == 'trimf':
        print(line[1], args[0], args[1], args[2])
        mf = TriangularMF(line[1], int(args[0]), int(args[1]), int(args[2]))

    if line[2] == 'tramf':
        print(line[1], args[0], args[1], args[2], args[3])
        mf = TrapezoidalMF(line[1], int(args[0]), int(args[1]), int(args[2]), int(args[3]))

    return mf


def parseVar(block):
    mfPattern = r'MF(.)*'
    namePattern = r'Name=(.)*'
    rangePattern = r'Range=(.)*'
    lines = block.split('\n')

    name = [l for l in lines if re.match(namePattern, l)][0]
    name = name.replace("'", "").split("=")[1]

    print(name)

    r = [l for l in lines if re.match(rangePattern, l)][0]
    r = r.replace("[", '').replace("]", '').split('=')[1].split(' ')

    mfs = []
    # print([line for line in lines if re.match(mfPattern, line)])
    for l in [line for line in lines if re.match(mfPattern, line)]:
        mfs.append(parseMF(l))

    print()

    return Input(name, (int(r[0]), int(r[1])), mfs)


if __name__ == "__main__":
    inPat = r'\[Input(.)*\]'
    outPat = r'\[Output(.)*\]'
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
    f = f.split('\n\n')

    inputs = []
    for block in [b for b in f if re.match(inPat, b)]:
        inputs.append(parseVar(block))

    outputs = []
    for block in [b for b in f if re.match(outPat, b)]:
        inputs.append(parseVar(block))


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
