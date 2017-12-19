#!/usr/bin/env python3
import numpy as np
import FLS
from FLS import Reasoner
from fisParser import parseFisFile


fFis = "fls/forward-V0_1.fis"
sFis = "fls/side-V0_1.fis"
v1Fis = "./fls/V0_1.fis"


# function taken from:
# https://stackoverflow.com/questions/31735499/calculate-angle-clockwise-between-two-points
def angle_between(p1, p2):
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    return (ang1 - ang2) % (2 * np.pi)


def calcDir(dl, dr, df, db, phi):
    forwFls = parseFisFile(fFis)
    sideFls = parseFisFile(sFis)
    forwFls = Reasoner(forwFls[3], forwFls[1], forwFls[2], 201, 'som')
    sideFls = Reasoner(sideFls[3], sideFls[1], sideFls[2], 201, 'som')

    inputForw = {'Distance-forward': df, 'Distance-backwards': db}
    inputSide = {'Distance-left': df, 'Distance-right': db}

    fDir = list(forwFls.inference(inputForw).values())[0]
    sDir = list(sideFls.inference(inputSide).values())[0]

    nDir = np.array([fDir, sDir])
    oDir = np.array([1, 0])

    angl = angle_between(oDir, nDir)

    phi = (phi + angl) % (2 * np.pi)

    return phi


def create_player_fls(filename):
    sysDict, inputs, outputs, rulebase = parseFisFile(filename)
    # create reasoner and return inference function
    reasoner = FLS.Reasoner(rulebase, inputs, outputs, 201,
                            sysDict['agg'], sysDict['defuzz'])
    return reasoner.inference
