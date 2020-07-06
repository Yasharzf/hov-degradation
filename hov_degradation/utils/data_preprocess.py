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


def get_neighbors(df_group_id):
    """ #TODO yf

    Parameters
    ----------
    df_group_id :
        pandas dataframe groupby object

    Return
    ------
    neighbors : dict

    """
    # get freeway names
    fwys = df_group_id.Fwy.unique()

    # get freeway types
    typs = df_group_id.Type.unique()

    neighbors = {}
    for fwy in fwys:
        for typ in typs:
            # find sorted ids
            _ids = df_group_id[
                (df_group_id['Fwy'] == fwy) &
                (df_group_id['Type'] == typ)].sort_values(by='Abs_PM').index
            for i, _id in enumerate(_ids):
                neighbors[_id] = {'up': None,
                                  'down': None,
                                  'main': None,
                                  'hov': None}
                # set upstream neighbors
                if i > 0:
                    neighbors[_id].update({'up': _ids[i - 1]})

                # set downstream neighbors
                if i < len(_ids) - 1:
                    neighbors[_id].update({'down': _ids[i + 1]})

                # set mainline neighbor of the HOV at the same location
                if typ == 'HV':
                    try:
                        main_neighbor_id = df_group_id[
                            (df_group_id['Fwy'] == fwy) &
                            (df_group_id['Type'] == 'ML') &
                            (df_group_id['Abs_PM'] == df_group_id.loc[
                                # FIXME set almost equal
                                _id, 'Abs_PM'])].index[0]
                        neighbors[_id].update({'main': main_neighbor_id})
                    except:
                        pass

                # set HOV neighbor of the mainline at the same location
                if typ == 'ML':
                    try:
                        hov_neighbor_id = df_group_id[
                            (df_group_id['Fwy'] == fwy) &
                            (df_group_id['Type'] == 'HV') &
                            (df_group_id['Abs_PM'] == df_group_id.loc[
                                # FIXME set almost equal
                                _id, 'Abs_PM'])].index[0]
                        neighbors[_id].update({'hov': hov_neighbor_id})
                    except:
                        pass
    return neighbors



