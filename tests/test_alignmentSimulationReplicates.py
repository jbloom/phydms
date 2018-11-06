"""Tests replicate simulations in aligment simulation.

Makes sure the replicate simulated alignments are different.

Written by Sarah Hilton and Jesse Bloom.
"""

import os
import sys
import scipy
import math
import unittest
import random
import io
import copy
import phydmslib.models
import phydmslib.treelikelihood
import phydmslib.simulate
from phydmslib.constants import *
import Bio.SeqIO
import Bio.Phylo
import pyvolve
import glob


class test_simulateAlignmentReplicate_ExpCM(unittest.TestCase):
    """Tests replicate functionality of `simulate.simulateAlignment`"""

    # use approach here to run multiple tests:
    # http://stackoverflow.com/questions/17260469/instantiate-python-unittest-testcase-with-arguments
    MODEL = phydmslib.models.ExpCM_empirical_phi

    def test_simulateAlignmentRandomSeed(self):
        """Simulate evolution, ensure replicats are different."""

        scipy.random.seed(1)
        random.seed(1)

        # define model
        nsites = 20
        prefs = []
        minpref = 0.01
        for r in range(nsites):
            rprefs = scipy.random.dirichlet([1] * N_AA)
            rprefs[rprefs < minpref] = minpref
            rprefs /= rprefs.sum()
            prefs.append(dict(zip(sorted(AA_TO_INDEX.keys()), rprefs)))
        kappa = 4.2
        omega = 0.4
        beta = 1.5
        mu = 0.3
        if self.MODEL == phydmslib.models.ExpCM:
            phi = scipy.random.dirichlet([7] * N_NT)
            model = phydmslib.models.ExpCM(prefs, kappa=kappa, omega=omega,
                                           beta=beta, mu=mu, phi=phi,
                                           freeparams=['mu'])
        elif self.MODEL == phydmslib.models.ExpCM_empirical_phi:
            g = scipy.random.dirichlet([7] * N_NT)
            model = phydmslib.models.ExpCM_empirical_phi(prefs, g, kappa=kappa,
                                                         omega=omega,
                                                         beta=beta, mu=mu,
                                                         freeparams=['mu'])
        elif self.MODEL == phydmslib.models.YNGKP_M0:
            e_pw = scipy.asarray([scipy.random.dirichlet([7] * N_NT) for i
                                  in range(3)])
            model = phydmslib.models.YNGKP_M0(e_pw, nsites)
        else:
            raise ValueError("Invalid MODEL: {0}".format(type(self.MODEL)))

        # make a test tree (two sequences separated by one branch)
        t = 0.04 / model.branchScale
        newicktree = '(tip1:{0},tip2:{0});'.format(t / 2.0)
        temptree = '_temp.tree'
        with open(temptree, 'w') as f:
            f.write(newicktree)

        nSim = 2
        seeds = [1, 1, 2]  # the first two runs should the the same
        alignments = [[{} for x in range(nSim)] for x in range(len(seeds))]
        for i, seed in enumerate(seeds):
            alignmentPrefix = "_test"
            final = ["{0}_{1}_simulatedalignment.fasta"
                     .format(alignmentPrefix, i) for i in range(nSim)]
            phydmslib.simulate.simulateAlignment(model, temptree,
                                                 alignmentPrefix, seed, nSim)
            for rep in range(nSim):
                for s in Bio.SeqIO.parse("_test_{0}_simulatedalignment.fasta"
                                         .format(rep), "fasta"):
                    alignments[i][rep][s.id] = str(s.seq)
            # clean-up
            for fasta in final:
                if os.path.isfile(fasta):
                    os.remove(fasta)
        os.remove(temptree)

        # sequence names
        seq_names = list(alignments[1][0].keys())

        # Within each run, the alignments should be different
        for i, seed in enumerate(seeds):
            run = alignments[i]
            for key in seq_names:
                seqs = [run[rep][key] for rep in range(nSim)]
                # all sequences should be different
                self.assertTrue(len(seqs) == len(set(seqs)))

        # The first two alignments should be the same, the third different
        for rep in range(nSim):
            for key in seq_names:
                seq1 = alignments[0][rep][key]
                seq2 = alignments[1][rep][key]
                seq3 = alignments[2][rep][key]
                self.assertTrue(seq1 == seq2)  # first two the same
                self.assertFalse(seq1 == seq3)  # third different


class test_simulateAlignmentReplicate_YNGKP_M0(test_simulateAlignmentReplicate_ExpCM):
    """Tests `simulateAlignment` of `YNGKP_M0` model."""
    MODEL = phydmslib.models.YNGKP_M0


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)
