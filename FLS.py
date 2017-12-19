#!/usr/bin/env python3
import numpy as np
from collections import Counter

# Membership Functions ########################################################


class TriangularMF:
    def __init__(self, name, a, b, c):
        self.name = name
        self.start = a
        self.top = b
        self.end = c

    def membership(self, x):
        # outside triangle
        if x < self.start or x > self.end:
            return 0
        # left half triangle
        elif x < self.top:
            return (x - self.start) / float(self.top - self.start)
        # top triangle
        elif self.top == self.end:
            return 1
        # right half triangle
        else:
            return (self.end - x) / float(self.end - self.top)


class TrapezoidalMF:
    def __init__(self, name, a, b, c, d):
        self.name = name
        self.start = a
        self.top_left = b
        self.top_right = c
        self.end = d

    def membership(self, x):
        # outside trapezoid
        if x < self.start or x > self.end:
            return 0
        # left slope trapezoid
        elif x < self.top_left:
            return (x - self.start) / float(self.top_left - self.start)
        # right slope trapezoid
        elif x > self.top_right:
            return (self.end - x) / float(self.end - self.top_right)
        # top trapezoid
        else:
            return 1


class GaussianMF:
    def __init__(self, name, m, s):
        self.name = name
        self.m = m
        self.s = s
        # calculate range outside of which values are basically zero
        offset = 1000**(1./2)*s
        self.start = m - offset
        self.end = m + offset

    def membership(self, x):
        return np.e**(-.5*((x - self.m) / float(self.s))**2)


class BellShapedMF:

    def __init__(self, name, m, s, a):
        # check for valid parameters
        assert a > 0, "Parameter value 'a' too small"
        self.name = name
        self.m = m
        self.s = s
        self.a = a
        # calculate range outside of which values are basically zero
        offset = 1000**(1./2/a)*s
        self.start = m - offset
        self.end = m + offset

    def membership(self, x):
        return 1 / float(1 + abs((x - self.m) / float(self.s))**(2 * self.a))


class SigmoidalMF:

    def __init__(self, name, a, c):
        self.name = name
        self.a = a
        self.c = c
        # calculate range outside of which values are basically zero
        offset = np.log(1000)/(-a)
        if offset < c:
            self.start = c + offset
            self.end = None
        else:
            self.start = None
            self.end = c + offset

    def membership(self, x):
        return 1 / float(1 + np.e**(-self.a*(x - self.c)))

###############################################################################

# Variables ###################################################################


class Variable:
    def __init__(self, name, r, mfs):
        self.name = name
        self.r = r
        self.mfs = mfs

    def membership(self, x):
        # TODO
#        assert x >= self.r[0] and x <= self.r[1], "Value out of range"
        if not (x >= self.r[0] and x <= self.r[1]):
            print(self.name)
            print(x)
            # print('[WARNING] Value out of range')
            # print('\t[TODO] cap variables in flsMovement.calcDir')
            # print('\t       and reinstate assert/exception')
        return {mf.name: mf.membership(x) for mf in self.mfs}

    # returns mf by name
    def get_mf(self, name):
        for mf in self.mfs:
            if mf.name == name:
                return mf


class Input(Variable):
    def __init__(self, name, r, mfs):
        super().__init__(name, r, mfs)
        self.type = 'input'


class Output(Variable):
    def __init__(self, name, r, mfs):
        super().__init__(name, r, mfs)
        self.type = 'output'

###############################################################################

# Rules #######################################################################


class Rule:
    def __init__(self, ant, op, con):
        self.ant_dict = ant
        self.op = op[0].upper()
        self.subop = op[1].upper()
        self.con_dict = con
        # check for correct operation names
        assert (self.op, self.subop) in [
            ("AND", "MIN"),
            ("AND", "PROD"),
            ("OR", "MAX"),
            ("OR", "PROBOR")
        ], "Invalid operation type"

    def get_fs(self, x_dict, inputs):
        if self.op == "AND":
            fs = 1
        elif self.op == "OR":
            fs = 0
        for cur_in in [i for i in inputs if i.name in self.ant_dict]:
            # make sure each input has a value
            assert cur_in.name in x_dict, "Insufficient data"
            # get membership value
            ant_fs = cur_in.get_mf(
                self.ant_dict[cur_in.name]
            ).membership(x_dict[cur_in.name])
            # combine inputs with rule operation
            if self.op == "AND":
                if self.subop == "MIN":
                    if ant_fs < fs:
                        fs = ant_fs
                elif self.subop == "PROD":
                    fs *= ant_fs
            elif self.op == "OR":
                if self.subop == "MAX":
                    if ant_fs > fs:
                        fs = ant_fs
                if self.subop == "PROBOR":
                    fs = fs + ant_fs - fs*ant_fs
        return fs


class Rulebase:
    def __init__(self, rules):
        self.rules = rules

    def get_fs(self, x_dict, inputs):
        result = {}
        for rule in self.rules:
            # calculate rule firing strength
            fs = rule.get_fs(x_dict, inputs)
            # collect all highest consequent firing stengths
            con_dict = rule.con_dict
            for con in con_dict:
                if con not in result:
                    result[con] = Counter()
                if fs > result[con][con_dict[con]]:
                    result[con][con_dict[con]] = fs
        return result

###############################################################################

# Reasoner ####################################################################
# TODO needs huge overhaul to support different types of
    # inference, aggregation and defuzzification
# TODO maybe make variable names shorter/more appropriate

class Reasoner:
    def __init__(self, rulebase, inputs, outputs, n_points, 
                 aggMethod, defuzzification):
        self.rulebase = rulebase
        self.inputs = inputs
        self.outputs = outputs
        self.discretize = n_points
        self.aggMethod = aggMethod.upper()
        self.defuzzification = defuzzification.upper()

    def inference(self, x_dict):
        # 1. Calculate the highest firing strength found in the rules per
        # membership function of the output variable
        # looks like: {"low":0.5, "medium":0.25, "high":0}
        fs_dict = self.rulebase.get_fs(x_dict, self.inputs)

        # 2. Aggragate and discretize
        # looks like: [(0.0, 1), (1.2437810945273631, 1),
        # (2.4875621890547261, 1), (3.7313432835820892, 1), ...]
        input_value_pairs = self.aggregate(fs_dict)

        # 3. Defuzzify
        # looks like a scalar
        crisp_outputs = self.defuzzify(input_value_pairs)
        return crisp_outputs

    def calc_mem_at_point(self, x, output, fs_dict):
        memberships = output.membership(x)
        values_at_x = []
        for (mf_name, fs) in fs_dict[output.name].items():
            values_at_x.append(min(memberships[mf_name], fs))

        # Maximum of values
        if self.aggMethod == 'MAX':
            pair = (x, max(values_at_x))

        # Sum of values
        elif self.aggMethod == 'SUM':
            pair = (x, sum(values_at_x))

        # elif self.aggMethod == 'PROBOR':
            # pass

        else:
            assert "Unknown aggregation method"

        return pair

    # TODO support more types of aggregation
    def aggregate(self, fs_dict):
        # First find where the aggrageted area starts and ends
        # Your code here
        input_value_pairs = {}
        for output in self.outputs:

            # Check whether any rules fired, else pass equivalent of None
            if len(fs_dict.get(output.name, [])) == 0:
                input_value_pairs[output.name] = None
                continue

            # determine relevant mf range
            end, start = output.r
            for mf_name in fs_dict[output.name].keys():
                mf = output.get_mf(mf_name)
                if mf.start is not None:
                    start = min(mf.start, start)
                if mf.end is not None:
                    end = max(mf.end, end)

            start = max(output.r[0], start)
            end = min(output.r[1], end)

            # Second discretize this area and aggragate
            cur_input_value_pairs = []
            stepSize = (end - start)/float(self.discretize)
            for x in np.arange(start, end, stepSize):
                pair = self.calc_mem_at_point(x, output, fs_dict)
                cur_input_value_pairs.append(pair)
            input_value_pairs[output.name] = cur_input_value_pairs
        return input_value_pairs

    def calc_crisp_value(self, curPairs):
        "Return the crips value based on the given area"

        # If no rules where fired for ouput
        if curPairs is None:
            return 0

        crispValue = 0
        inputValues = [pairs[1] for pairs in curPairs]

        # Smallest of max
        if self.defuzzification == "SOM":
            i = inputValues.index(max(inputValues))
            crispValue = curPairs[i][0]

        # least of max
        elif self.defuzzification == "LOM":
            i = -inputValues[::-1].index(max(inputValues)) - 1
            crispValue = curPairs[i][0]

        # mean of max
        elif self.defuzzification == 'MOM':
            m = max(inputValues)
            crispValue = np.mean([x[0] for x in curPairs if x[1] == m])

        # Centroid / Center of Gravity / center of Area
        elif (self.defuzzification == 'COG'
              or self.defuzzification == 'COA'
              or self.defuzzification == 'CENTROID'):
            tmp1 = np.sum([x[0] * x[1] for x in curPairs])
            tmp2 = np.sum(inputValues)
            crispValue = tmp1 / tmp2

        else:
            assert('Defuzzyfy operation unknown')

        return crispValue

    def defuzzify(self, input_value_pairs):
        crisp_values = {}
        for (output_name, cur_input_value_pairs) in input_value_pairs.items():
            crisp_values[output_name] = self.calc_crisp_value(cur_input_value_pairs)
        return crisp_values

###############################################################################

# Tests #######################################################################
# TODO to be removed at some point
# also the matplotlib import (that's why I put it here)
import matplotlib.pyplot as plt

# not used anymore
def pltMF(mf, p, q):
    t = np.arange(p, q, .01)
    mfr = []
    for x in t:
        mfr.append(mf.membership(x))
    plt.figure()
    plt.plot(t, mfr, label=mf.name)
    plt.legend()
    plt.show()


def plot_var(var):
    x = np.arange(var.r[0], var.r[1], (var.r[1]-var.r[0])/100.)
    plt.figure()
    for i in range(len(var.mfs)):
        mem = []
        for xx in x:
            mem.append(var.mfs[i].membership(xx))
        plt.plot(x, mem, color='C'+str(i))
    plt.show()
    return


if __name__ == "__main__":

    # Input variable for your income
    # Your code here
    mfs_income = [
        TrapezoidalMF("low", 0, 0, 200, 400),
        TriangularMF("medium", 200, 500, 800),
        TrapezoidalMF("high", 600, 800, 1000, 1000)
    ]
    income = Input("income", (0, 1000), mfs_income)

    # Input variable for the quality
    # Your code here
    mfs_quality = [
        TrapezoidalMF("bad", 0, 0, 2, 4),
        TriangularMF("okay", 2, 5, 8),
        TrapezoidalMF("amazing", 6, 8, 10, 10)
    ]
    quality = Input("quality", (0, 10), mfs_quality)

    # Output variable for the amount of money
    # Your code here
    mfs_money = [
        TrapezoidalMF("low", 0, 0, 100, 250),
        TriangularMF("medium", 150, 250, 350),
        TrapezoidalMF("high", 250, 400, 500, 500),
    ]
    money = Output("money", (0, 500), mfs_money)
    money2 = Output("money2", (0, 500), mfs_money)

    inputs = [income, quality]
    outputs = [money, money2]

    #print(income.membership(489))
    #print(quality.membership(6))
    #print(money.membership(222))

    #plot_var(income)
    #plot_var(quality)
    #plot_var(money)

    rule1 = Rule(
        {"income":"low", "quality":"amazing"}, ("and", "min"), {"money":"low"}
    )
    #print(rule1.get_fs({"income":200, "quality":6.5}, inputs))
    #print(rule1.get_fs({"income":0, "quality":10}, inputs))

    rule2 = Rule(
        {"income":"high", "quality":"bad"}, ("and", "min"), {"money":"high"}
    )
    #print(rule2.get_fs({"income":100, "quality":8}, inputs))
    #print(rule2.get_fs({"income":700, "quality":3}, inputs))


    # RULEBASE
    # Add the rules listed in the question description
    # Your code here
    rules = [
        Rule({"income":"low", "quality":"amazing"}, ("and", "min"), {"money":"low", "money2":"low"}),
        Rule({"income":"medium", "quality":"amazing"}, ("and", "min"), {"money":"low", "money2":"low"}),
        Rule({"income":"high", "quality":"amazing"}, ("and", "min"), {"money":"low", "money2":"low"}),
        Rule({"income":"low", "quality":"okay"}, ("and", "min"), {"money":"low"}),
        Rule({"income":"medium", "quality":"okay"}, ("and", "min"), {"money":"medium", "money2":"low"}),
        Rule({"income":"high", "quality":"okay"}, ("and", "min"), {"money":"medium", "money2":"low"}),
        Rule({"income":"low", "quality":"bad"}, ("and", "min"), {"money":"low"}), # TODO note: has no money2 value
        Rule({"income":"medium", "quality":"bad"}, ("and", "min"), {"money":"medium", "money2":"low"}),
        Rule({"income":"high", "quality":"bad"}, ("and", "min"), {"money":"high", "money2":"low"})
    ]
    rulebase = Rulebase(rules)
    # Test your implementation of calculate_firing_strengths()
    # Enter your answers in the Google form to check them, round to two decimals
    datapoint = {"income":500, "quality":3}
    #print(rulebase.get_fs(datapoint, inputs))
    datapoint = {"income":234, "quality":7.5}
    #print(rulebase.get_fs(datapoint, inputs))


    # REASONER
    # Test your implementation of the fuzzy inference
    # Enter your answers in the Google form to check them, round to two decimals

    thinker = Reasoner(rulebase, inputs, outputs, 201, 'max', "som")
    datapoint = {"income":100, "quality":1}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 101, 'max', "som")
    datapoint = {"income":550, "quality":4.5}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 201, 'max', "som")
    datapoint = {"income":900, "quality":6.5}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 201, 'max', "lom")
    datapoint = {"income":100, "quality":1}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 101, 'max', "lom")
    datapoint = {"income":550, "quality":4.5}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 201, 'max', "lom")
    datapoint = {"income":900, "quality":6.5}
    print(thinker.inference(datapoint))


    # TODO
    # print("[!] Further testing needs to be done by comparing results to MATLAB")
    # print("    and using different membership functions and rule operations.")

    ###############################################################################

