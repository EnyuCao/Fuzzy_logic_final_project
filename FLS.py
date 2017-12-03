import numpy as np
from collections import Counter

# Membership Functions ########################################################

class TriangularMF:
    def __init__(self, name, a, b, c):
        self.name = name
        self.a = a
        self.b = b
        self.c = c
    def membership(self, x):
        if x < self.a or x > self.c:
            return 0
        elif x < self.b:
            return (x - self.a) / float(self.b - self.a)
        elif self.b == self.c:
            return 1
        else:
            return (self.c - x) / float(self.c - self.b)

class TrapezoidalMF:
    def __init__(self, name, a, b, c, d):
        self.name = name
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    def membership(self, x):
        if x < self.a or x > self.d:
            return 0
        elif x < self.b:
            return (x - self.a) / float(self.b - self.a)
        elif x > self.c:
            return (self.d - x) / float(self.d - self.c)
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
        assert x > self.r[0] and x < self.r[1], 'Value out of range'
        return {mf.name:mf.membership(x) for mf in self.mfs}
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



###############################################################################



# Tests #######################################################################

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
        plt.scatter(x, mem, color='C'+str(i), s=5)
    plt.show()
    return

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
output = money

#print(income.membership(489))
#print(quality.membership(6))
#print(output.membership(222))

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


# TODO
print("[!] Further testing needs to be done by comparing results to MATLAB")
print("    and using different membership functions and rule operations.")
###############################################################################

