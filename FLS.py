#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# Membership Functions ########################################################


class TriangularMF:
    def __init__(self, name, a, b, c):
        self.name = name
        self.start = a
        self.top = b
        self.end = c

    def membership(self, x):
        if x < self.start or x > self.end:
            return 0
        elif x < self.top:
            return (x - self.start) / float(self.top - self.start)
        elif self.top == self.end:
            return 1
        else:
            return (self.end - x) / float(self.end - self.top)


class TrapezoidalMF:
    def __init__(self, name, a, b, c, d):
        self.name = name
        self.start = a
        self.topl = b
        self.topr = c
        self.end = d

    def membership(self, x):
        if x < self.start or x > self.end:
            return 0
        elif x < self.topl:
            return (x - self.start) / float(self.topl - self.start)
        elif x > self.topr:
            return (self.end - x) / float(self.end - self.topr)
        else:
            return 1


class GaussianMF:
    def __init__(self, name, m, s):
        self.name = name
        self.m = m
        self.s = s

    def membership(self, x):
        return np.e**(-.5*((x - self.m) / float(self.s))**2)


class BellShapedMF:

    def __init__(self, name, m, s, a):
        self.name = name
        self.m = m
        self.s = s
        self.a = a

    def membership(self, x):
        return 1 / float(1 + abs((x - self.m) / float(self.s))**(2 * self.a))


class SigmoidalMF:

    def __init__(self, name, a, c):
        self.name = name
        self.a = a
        self.c = c

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
        return {mf.name: mf.membership(x) for mf in self.mfs}

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
            assert cur_in.name in x_dict, "Insufficient data"
            ant_fs = cur_in.get_mf(
                self.ant_dict[cur_in.name]
            ).membership(x_dict[cur_in.name])
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
            fs = rule.get_fs(x_dict, inputs)
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
# TODO also, breaks for anything but TriangularMFs and TrapezoidalMFs
# TODO maybe make variable names shorter/more appropriate

class Reasoner:
    def __init__(self, rulebase, inputs, outputs, n_points, defuzzification):
        self.rulebase = rulebase
        self.inputs = inputs
        self.outputs = outputs
        self.discretize = n_points
        self.defuzzification = defuzzification.upper()

    def inference(self, x_dict):
        # 1. Calculate the highest firing strength found in the rules per 
        # membership function of the output variable
        # looks like: {"low":0.5, "medium":0.25, "high":0}
        fs_dict = self.rulebase.get_fs(x_dict, self.inputs)

        # 2. Aggragate and discretize
        # looks like: [(0.0, 1), (1.2437810945273631, 1), (2.4875621890547261, 1), (3.7313432835820892, 1), ...]
        input_value_pairs = self.aggregate(fs_dict)

        # 3. Defuzzify
        # looks like a scalar
        crisp_outputs = self.defuzzify(input_value_pairs)
        return crisp_outputs

    # TODO support more types of aggregation
    def aggregate(self, fs_dict):
        # First find where the aggrageted area starts and ends
        # Your code here
        input_value_pairs = {}
        for output in self.outputs:
            end, start = output.r
            for mf_name in fs_dict[output.name].keys():
                mf = output.get_mf(mf_name)
                # TODO only supports TriangularMFs and TrapezoidalMFs
                start = mf.start if mf.start < start else start
                end = mf.end if mf.end > end else end
            # Second discretize this area and aggragate
            cur_input_value_pairs = []
            for x in np.arange(
                start, end, (end - start)/float(self.discretize)
            ):
                memberships = output.membership(x)
                values_at_x = []
                for (mf_name, fs) in fs_dict[output.name].items():
                    values_at_x.append(min(memberships[mf_name], fs))
                cur_input_value_pairs.append((x, max(values_at_x)))
            input_value_pairs[output.name] = cur_input_value_pairs
        return input_value_pairs

    # TODO support more types of defuzzification
    def defuzzify(self, input_value_pairs):
        crisp_values = {}
        for (output_name, cur_input_value_pairs) in input_value_pairs.items():
            crisp_value = 0
            input_values = [pairs[1] for pairs in cur_input_value_pairs]
            if self.defuzzification == "SOM":
                crisp_value = cur_input_value_pairs[
                    input_values.index(max(input_values))
                ][0]
            elif self.defuzzification == "LOM":
                crisp_value = cur_input_value_pairs[
                    -input_values[::-1].index(max(input_values)) - 1
                ][0]
            crisp_values[output_name] = crisp_value
        return crisp_values

###############################################################################

# Tests #######################################################################


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
        plt.scatter(x, mem, color='C'+str(i), s=5)
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
        TrapezoidalMF("high", 250, 400, 500, 500)
    ]
    money = Output("money", (0, 500), mfs_money)

    inputs = [income, quality]
    outputs = [money]

    #print(income.membership(489))
    #print(quality.membership(6))
    #print(money.membership(222))

    # plot_var(income)
    # plot_var(quality)
    # plot_var(money)

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
    #print(rulebase.get_fs(datapoint, inputs))
    datapoint = {"income":234, "quality":7.5}
    #print(rulebase.get_fs(datapoint, inputs))


    # REASONER
    # Test your implementation of the fuzzy inference
    # Enter your answers in the Google form to check them, round to two decimals

    thinker = Reasoner(rulebase, inputs, outputs, 201, "som")
    datapoint = {"income":100, "quality":1}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 101, "som")
    datapoint = {"income":550, "quality":4.5}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 201, "som")
    datapoint = {"income":900, "quality":6.5}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 201, "lom")
    datapoint = {"income":100, "quality":1}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 101, "lom")
    datapoint = {"income":550, "quality":4.5}
    print(thinker.inference(datapoint))

    thinker = Reasoner(rulebase, inputs, outputs, 201, "lom")
    datapoint = {"income":900, "quality":6.5}
    print(thinker.inference(datapoint))


    # TODO
    # print("[!] Further testing needs to be done by comparing results to MATLAB")
    # print("    and using different membership functions and rule operations.")

    ###############################################################################
