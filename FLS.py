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
        # make sure value is in variables range
        assert x >= self.r[0] and x <= self.r[1], "Value out of range"
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
        # Collect all membership values for the given output
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

        else:
            assert "Unknown aggregation method"

        return pair

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
                if type(start) == type(None):
                    start = output.r[0]
                else:
                    start = mf.start if mf.start < start else start
                if type(end) == type(None):
                    end = output.r[1]
                else:
                    end = mf.end if mf.end > end else end

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

