"""Runs the model adequacy protocol.

This test examines the functionality of the model adequcy protocol and checks
the results against the output in `expected_modeladequacy_results`.

All of the runs using multiprocessing.

Written by Sarah Hilton.
"""

import unittest
import phydmslib.simulate
import phydmslib.file_io
import phydmslib.modeladequacy
from phydmslib.constants import *
import os
from statsmodels.sandbox.stats.multicomp import multipletests
import scipy
import numpy as np
import itertools
import pandas as pd
import cProfile
import pstats
import glob
import subprocess


class test_modeladequacy_ExpCM_seed0(unittest.TestCase):
    """Runs model adequacy on an ExpCM."""
    # run parameters
    MODEL = "ExpCM_{0}".format(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "modeladequacy_tests/HA_short_prefs_nsites10.csv"))
    EXPECTED = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "expected_modeladequacy_results/ExpCM_pvalues_seed0.csv")
    TREE = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        "modeladequacy_tests/HA_short_nsites10_nseqs34_tree.newick")
    SEED = 0

    def test_modeladequacy(self):
        """Runs model adequacy and compares against expected results."""
        n_sim = 100
        alignment = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 "modeladequacy_tests/HA_short_nsites10_nseqs34.fasta")
        outprefix = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                 "_model_adequacy_results")
        tree = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "modeladequacy_tests/HA_short_nsites10_nseqs34_tree.newick")
        cmd = ["phydms_modeladequacy", outprefix, alignment,
               self.MODEL, "--number_simulations", str(n_sim), "--tree", tree,
               "--seed", str(self.SEED)]
        subprocess.check_call(cmd)

        final = (pd.read_csv("{0}_pvalues.csv".format(outprefix))
                 .sort_values(by=["site", "metric"]))
        expected = (pd.read_csv(self.EXPECTED)
                    .sort_values(by=["site", "metric"]))

        self.assertTrue(scipy.allclose(final["pvalue"], expected["pvalue"]))
        self.assertTrue(scipy.allclose(final["qvalue"], expected["qvalue"]))

        # remove files
        for fname in glob.glob("{0}_*".format(outprefix)):
            os.remove(fname)


class test_modeladequacy_ExpCM_seed1(test_modeladequacy_ExpCM_seed0):
    """Runs model adequacy on an ExpCM with a seed of 1."""
    # run parameters
    EXPECTED = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "expected_modeladequacy_results/ExpCM_pvalues_seed1.csv")
    SEED = 1


class test_modeladequacy_YNGKPM0_seed0(test_modeladequacy_ExpCM_seed0):
    """Runs model adequacy on a YNGKP_M0 with seed of 0."""
    # run parameters
    MODEL = "YNGKP_M0"
    EXPECTED = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "expected_modeladequacy_results/YNGKP_M0_pvalues_seed0.csv")


class test_modeladequacy_YNGKPM0_seed1(test_modeladequacy_YNGKPM0_seed0):
    """Runs model adequacy on a YNGKP_M0 with seed of 1."""
    # run parameters
    SEED = 1
    EXPECTED = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "expected_modeladequacy_results/YNGKP_M0_pvalues_seed1.csv")

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)