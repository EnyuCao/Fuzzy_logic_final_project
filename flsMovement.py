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


# Used for an older version of the FLS, outdated
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


def create_player_fls_from_fis(filename):
    """ uses the fisParser to create a Reasoner """
    sysDict, inputs, outputs, rulebase = parseFisFile(filename)
    # create reasoner and return inference function
    reasoner = FLS.Reasoner(rulebase, inputs, outputs, 201,
                            sysDict['agg'], sysDict['defuzz'])
    return reasoner.inference


def create_player_fls(r_dist, r_phi, n_points=201,
                      aggregation='max', defuzzification='lom'):
    """
    Creates the FLS used when testing.
    The Created FLS is the same as in ./fls/V1.fis
    """
    # create inputs
    mfs_dist = [
        FLS.TrapezoidalMF('low', r_dist[0],r_dist[0],r_dist[1],r_dist[2]),
        FLS.TriangularMF('medium', r_dist[1],r_dist[2],r_dist[3]),
        FLS.TrapezoidalMF('high', r_dist[2],r_dist[3],r_dist[4],r_dist[4]),
    ]
    distf = FLS.Input('distf', (r_dist[0], r_dist[-1]), mfs_dist)
    distl = FLS.Input('distl', (r_dist[0], r_dist[-1]), mfs_dist)
    distr = FLS.Input('distr', (r_dist[0], r_dist[-1]), mfs_dist)
    inputs = [distf, distl, distr]

    # create outputs
    mfs_phi = [
        FLS.TrapezoidalMF('low', r_phi[0],r_phi[0],r_phi[1],r_phi[2]),
        FLS.TriangularMF('medium', r_phi[1],r_phi[2],r_phi[3]),
        FLS.TrapezoidalMF('high', r_phi[2],r_phi[3],r_phi[4],r_phi[4]),
    ]
    phil = FLS.Output('phil', (r_phi[0], r_phi[-1]), mfs_phi)
    phir = FLS.Output('phir', (r_phi[0], r_phi[-1]), mfs_phi)
    outputs = [phil, phir]

    # create rulebase
    rules = [
        FLS.Rule(
            {'distf':'low', 'distl':'low', 'distr':'low'},
            ('and', 'min'),
            {'phil':'high', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'low', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'low', 'phir':'high'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'low', 'distr':'high'},
            ('and', 'min'),
            {'phil':'low', 'phir':'high'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'medium', 'distr':'low'},
            ('and', 'min'),
            {'phil':'high', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'medium', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'high', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'medium', 'distr':'high'},
            ('and', 'min'),
            {'phil':'low', 'phir':'high'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'high', 'distr':'low'},
            ('and', 'min'),
            {'phil':'high', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'high', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'high', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'low', 'distl':'high', 'distr':'high'},
            ('and', 'min'),
            {'phil':'high', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'low', 'distr':'low'},
            ('and', 'min'),
            {'phil':'low', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'low', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'low', 'phir':'medium'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'low', 'distr':'high'},
            ('and', 'min'),
            {'phil':'low', 'phir':'high'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'medium', 'distr':'low'},
            ('and', 'min'),
            {'phil':'medium', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'medium', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'medium', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'medium', 'distr':'high'},
            ('and', 'min'),
            {'phil':'medium', 'phir':'high'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'high', 'distr':'low'},
            ('and', 'min'),
            {'phil':'high', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'high', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'high', 'phir':'medium'}
        ),
        FLS.Rule(
            {'distf':'medium', 'distl':'high', 'distr':'high'},
            ('and', 'min'),
            {'phil':'high', 'phir':'medium'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'low', 'distr':'low'},
            ('and', 'min'),
            {'phil':'low', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'low', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'low', 'phir':'medium'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'low', 'distr':'high'},
            ('and', 'min'),
            {'phil':'low', 'phir':'medium'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'medium', 'distr':'low'},
            ('and', 'min'),
            {'phil':'medium', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'medium', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'low', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'medium', 'distr':'high'},
            ('and', 'min'),
            {'phil':'low', 'phir':'medium'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'high', 'distr':'low'},
            ('and', 'min'),
            {'phil':'medium', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'high', 'distr':'medium'},
            ('and', 'min'),
            {'phil':'medium', 'phir':'low'}
        ),
        FLS.Rule(
            {'distf':'high', 'distl':'high', 'distr':'high'},
            ('and', 'min'),
            {'phil':'medium', 'phir':'medium'}
        ),
    ]
    rulebase = FLS.Rulebase(rules)
    # create reasoner and return inference function
    reasoner = FLS.Reasoner(
        rulebase, inputs, outputs, n_points, aggregation, defuzzification
    )
    return reasoner.inference
