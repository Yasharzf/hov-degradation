"""Script to preprocess PeMS Station 5-Minute data"""
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

FREEWAYS = {
    210: {
        'name': 'I210',
        'dirs': ['E', 'W'],
        'range_min': 22.6,
        'range_max': 41.4
    },
    134: {
        'name': 'SR134',
        'dirs': ['E', 'W'],
        'range_min': 11.4,
        'range_max': 13.5
    },
    605: {
        'name': 'I605',
        'dirs': ['N', 'S'],
        'range_min': 25.3,
        'range_max': 28.0
    }
}


def get_ks_stats(X, neighbors):
    """ #TODO yf

    Parameters
    ----------
    X :

    neighbors :

    Return
    ------
    ks_down :

    ks_up :


    """
    ks_down = pd.DataFrame(index=X.index, columns=['statistic', 'p-value'])
    ks_up = pd.DataFrame(index=X.index, columns=['statistic', 'p-value'])

    inds = X.index

    for ind in inds:
        try:
            X_up = X.loc[neighbors[ind]['up']]
            ks_up.loc[ind, :] = ks_2samp(X.loc[ind].values, X_up.values)
        except:
            pass
        try:
            X_down = X.loc[neighbors[ind]['down']]
            ks_down.loc[ind, :] = ks_2samp(X.loc[ind].values, X_down.values)
        except:
            pass
    ks_stats = {'up': ks_up, 'down': ks_down}
    return ks_stats



