"""Functions for performing model adequacy tests.

Written by Sarah Hilton.
"""

from phydmslib.constants import *
import phydmslib.models
import pandas as pd
import scipy
import math


def translate_with_gaps(seq):
    """Translate from nucleotides to amino acids.

    Args:
        `seq` (str)
            The nucleotide sequence.
    Returns:
        The amino-acid sequence

    >>> s1 = "ATGATG"
    >>> s2 = "CTT---ATG"
    >>> translate_with_gaps(s1) == "MM"
    True
    >>> translate_with_gaps(s2) == "L-M"
    True

    """
    assert len(seq) % 3 == 0, "Sequence is not divisible by 3."
    prot_seq = []
    for i in range(0, len(seq), 3):
        codon = seq[i:i+3]
        if codon == "---":
            aa = "-"
        else:
            codon = CODON_TO_INDEX[codon]
            aa = INDEX_TO_AA[CODON_TO_AA[codon]]
        prot_seq.append(aa)
    return "".join(prot_seq)


def calc_aa_frequencies(alignment):
    """Calculate amino-acid frequencies from a codon alignment.

    Args:
        `alignment` (list)
            Alignment of codon sequences as a list of tuples, (seq_id, seq)
    Returns:
        `pandas` dataframe of amino-acid frequencies by site

    >>> answer = pd.DataFrame({"site": [1, 2], "A": [0.0, 0.0],\
                               "C": [0.0, 0.0], "D": [0.0, 0.0],\
                               "E": [0.0, 0.0], "F": [0.0, 0.0],\
                               "G": [0.0, 0.0], "H": [0.0, 0.0],\
                               "I": [0.0, 0.0], "K": [0.0, 0.0],\
                               "L": [0.0, 0.0], "M": [0.0, 0.0],\
                               "N": [0.0, 0.0], "P": [0.0, 0.0],\
                               "Q": [0.0, 0.0], "R": [0.0, 0.0],\
                               "S": [0.0, 0.0], "T": [0.0, 0.0],\
                               "V": [0.0, 0.0], "W": [0.0, 0.0],\
                               "Y": [0.0, 0.0]}, columns=["site","A","C",\
                                                          "D","E","F","G",\
                                                          "H","I","K","L",\
                                                          "M","N","P","Q",\
                                                          "R","S","T","V",\
                                                          "W","Y"])
    >>> align1 = [("seq_1", "ATGATG"), ("seq_2", "CTTATG")]
    >>> align2 = [("seq_1", "ATGATG"), ("seq_2", "CTT---")]
    >>> answer1 = answer.copy()
    >>> answer1[["L", "M"]] = pd.DataFrame({"L": [0.5, 0.0],\
                                            "M": [0.5, 1.0]})
    >>> answer1.equals(calc_aa_frequencies(align1))
    True
    >>> answer1.equals(calc_aa_frequencies(align2))
    True

    """
    # Read in the alignnment
    assert scipy.all(scipy.array([len(s[1]) % 3 for s in alignment]) == 0),\
        "At least one sequence in the alignment is not a multiple of 3."
    seqlength = len(alignment[0][1]) // 3
    df = {k: [0 for x in range(seqlength)] for k in list(INDEX_TO_AA.values())}

    # count amino acid frequencies
    for seq in alignment:
        for i, aa in enumerate(translate_with_gaps(seq[1])):
            if aa != '-':
                df[aa][i] += 1
    df = pd.DataFrame(df)

    # Normalize the dataframe
    assert not scipy.any(df.sum(axis=1) == 0), ("Attempting to normalize a "
                                                "site by an amino acid count"
                                                " of zero. Does the alignment"
                                                " have an all gap column?")
    df = df.div(df.sum(axis=1), axis=0)
    assert scipy.allclose(df.sum(axis=1), 1, atol=0.005)

    # Final formatting
    aa = [x for x in INDEX_TO_AA.values()]
    aa.sort()  # ABC order
    final_cols = ["site"]
    final_cols.extend(aa)
    df["site"] = [x+1 for x in range(len(df))]
    df = df[final_cols]
    return df


def prefDistance(pi1, pi2, distmetric):
    """Compute the distance between two arrays of preferences.

    Args:
        `pi1` and `pi2` (array-like)
            Two arrays of preferences.
        `distmetric` (string)
            Distance metric to use. Can be:
                - `half_sum_abs_diff`: half sum absolute value of difference
                - `JensenShannon`: square root of Jensen-Shannon divergence

    Returns:
        The distance between `pi1` and `pi2`.

    >>> pi1 = [0.5, 0.2, 0.3]
    >>> pi2 = [0.2, 0.4, 0.4]
    >>> scipy.allclose(prefDistance(pi1, pi1, 'half_sum_abs_diff'), 0)
    True
    >>> scipy.allclose(prefDistance(pi1, pi1, 'JensenShannon'), 0)
    True
    >>> scipy.allclose(prefDistance(pi1, pi2, 'half_sum_abs_diff'), 0.3)
    True
    >>> scipy.allclose(prefDistance(pi1, pi2, 'JensenShannon'), 0.2785483)
    True

    """
    pi1 = scipy.array(pi1)
    pi2 = scipy.array(pi2)
    assert len(pi1) == len(pi2)
    assert scipy.allclose(pi1.sum(), 1, atol=0.005)
    assert scipy.allclose(pi2.sum(), 1, atol=0.005)
    assert scipy.all(pi1 >= 0)
    assert scipy.all(pi2 >= 0)

    if distmetric == 'half_sum_abs_diff':
        dist = (scipy.fabs(pi1 - pi2)).sum() / 2.0

    elif distmetric == 'JensenShannon':
        dist = math.sqrt(divJensenShannon(pi1, pi2))

    else:
        raise ValueError('Invalid `distmetric` {0}'.format(distmetric))

    return dist


def divJensenShannon(p1, p2):
    """Jensen-Shannon divergence between two distributions.

    The logarithms are taken to base 2, so the result will be
    between 0 and 1.
    Args:
        `p1` and `p2` (array-like)
            The two distributions for which we compute divergence.
    Returns:
        The Jensen-Shannon divergence as a float.
    >>> p1 = [0.5, 0.2, 0.2, 0.1]
    >>> p2 = [0.4, 0.1, 0.3, 0.2]
    >>> p3 = [0.0, 0.2, 0.2, 0.6]
    >>> scipy.allclose(divJensenShannon(p1, p1), 0, atol=1e-5)
    True
    >>> scipy.allclose(divJensenShannon(p1, p2), 0.035789, atol=1e-5)
    True
    >>> scipy.allclose(divJensenShannon(p1, p3), 0.392914, atol=1e-5)
    True

    """
    p1 = scipy.array(p1)
    p2 = scipy.array(p2)

    def _kldiv(a, b):
        with scipy.errstate(all='ignore'):
            kl = a * scipy.log2(a / b)
            kl = scipy.nansum(kl)
        return kl

    m = 0.5 * (p1 + p2)

    return 0.5 * (_kldiv(p1, m) + _kldiv(p2, m))


def calc_stationary_state_freqs(model):
    """Calculate the stationary state amino-acids frequencies of a model.

    Args:
        `model` (phydmslib.models.ExpCM)

    Returns:
        frequencies (`numpy.ndarray` of floats)
            The stationary state amino-acid frequencies.
            frequencies[r][a] is the statioanry state frequence of amino acid
            `a` at site `r`.

    """
    def _calc_aa_freq(aa, ss):
        """Calc the frequency of a single site/amino acid pair."""
        codon_indices = scipy.where(CODON_TO_AA == aa)[0]
        return ss[codon_indices].sum()

    frequencies = []
    for r in range(model.nsites):
        aminoacid_ss = scipy.array([_calc_aa_freq(aa, model.stationarystate[r])
                                    for aa in range(N_AA)])
        frequencies.append(aminoacid_ss)
    return scipy.array(frequencies)


def make_expcm(model_fname, prefs):
    """Make an ExpCM from a model params file."""
    params = pd.read_csv(model_fname, engine="python", sep=" = ", header=None)
    params = dict(zip(params[0], params[1]))
    params["phiT"] = 1 - sum([params[x] for x in params.keys()
                             if x.startswith("phi")])
    phi = scipy.array([params["phi{0}".format(INDEX_TO_NT[x])]
                       for x in range(N_NT)])
    return phydmslib.models.ExpCM(prefs, kappa=params["kappa"],
                                  omega=params["omega"], beta=params["beta"],
                                  mu=0.3, phi=phi, freeparams=['mu'])


def make_YNGKP_M0(model_fname, nsites):
    """Make an YNGKP_M0 from a model params file."""
    params = pd.read_csv(model_fname, engine="python", sep=" = ", header=None)
    params = dict(zip(params[0], params[1]))
    e_pw = scipy.zeros((3, N_NT))
    for key in params.keys():
        if key.startswith("phi"):
            p = int(key[-2])
            w = int(NT_TO_INDEX[key[-1]])
            e_pw[p][w] = params[key]
        elif key == "kappa":
            kappa = params[key]
        elif key == "omega":
            omega = params[key]
        else:
            raise ValueError("Unexpected parameter {0}".format(key))
    for p in range(3):
        e_pw[p][3] = 1 - e_pw[p].sum()
    return phydmslib.models.YNGKP_M0(e_pw, nsites, kappa=kappa, omega=omega,
                                     mu=1.0, freeparams=['mu'])


def calculate_pvalue(simulation_values, true_value, seed=False):
    """Calculate pvalue based on simuation distribution.

    The p value is defined as (# simulations greater than true + 1) /
    (# simulations +1).

    In the case where there is at least one simulation with the exact
    same value as the true value, the number of "tied" simulations
    which will be recorded as "greater" will be randomly determined.

    Args:
        `simulation_values` (list)
            List of simulation values.
        `true_value` (`float`)
            True value to calculate p value for.
        `seed` (`int` or `False`)
            Seed used to randomly break ties.
    Returns:
        The p value as a float.
    >>> true = 10
    >>> print("{:1.1f}".format(calculate_pvalue([1, 2, 3, 4], true)))
    0.2
    >>> print("{:1.1f}".format(calculate_pvalue([11, 12, 13, 14], true)))
    1.0
    >>> print("{:1.1f}".format(calculate_pvalue([3, 4, 12, 9], true)))
    0.4
    >>> print("{:1.1f}".format(calculate_pvalue([1, 10, 10, 11], true, 1)))
    0.6

    """
    if seed is not False:
        scipy.random.seed(seed)
    assert len(simulation_values) >= 2, "Must have at least two simulations."
    greater = scipy.sum(scipy.greater(simulation_values, true_value))
    tie_breaker = scipy.sum(scipy.equal(simulation_values, true_value))
    if tie_breaker >= 1:
        tie_breaker = scipy.random.randint(tie_breaker, size=1)[0]
    pvalue = (greater + tie_breaker + 1) / (len(simulation_values) + 1)
    assert 0 <= pvalue <= 1.0, "pvalue is > 1.0 or < 0.0"
    return pvalue


if __name__ == '__main__':
    import doctest
    doctest.testmod()
