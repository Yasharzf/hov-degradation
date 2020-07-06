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


def usable_stations(df_merge):
    """ #TODO yf

    Parameters
    ----------
    df_merge :
        pandas dataframe

    Return
    ------
    usable :

    """
    group = df_merge.groupby('ID')
    num_times = len(df_merge['Timestamp'].unique())

    # Find IDS that report Flow for more than half of the timestamps
    fidx = group['Flow'].count() > (num_times / 2)

    # Find IDS that report at least 5 samples per lane
    sidx = group['Samples'].mean() / group.first()['Lanes'] > 5.0

    # Find IDs that report mean observation > 50%
    oidx = group['Observed'].mean() > 50

    usable = fidx & sidx & oidx
    return usable


def apply_misconfiguration(df_merge, ratio=0.30):
    """ #TODO yf

    Parameters
    ----------
    data :
        pandas dataframe

    Return
    ------
    data :

    """
    # create new columns for swapped data, initialize based on ground truth
    df_merge['misconfigured'] = 0
    df_merge['swapped_lane_num'] = None

    df_group_id = df_merge.groupby('ID').first()

    # filter
    hov_data = df_group_id[df_group_id.Type == 'HV']

    # randomly select stations
    np.random.seed(12345678)

    misconfigured_inds = np.random.randint(low=0,
                                           high=hov_data.shape[0],
                                           size=int(hov_data.shape[0] * ratio))
    misconfigured_ids = hov_data.iloc[misconfigured_inds].index

    # assign label to misconfigured stations

    # get neighbors
    neighbors = get_neighbors(df_group_id)

    # swap hov info (Flow and Occupancies) with a random lane in mainline
    for _id in misconfigured_ids:
        df_merge.loc[df_merge.ID == _id, 'misconfigured'] = 1

        # get neighbor in mainline
        neighbor_ml_id = neighbors[_id]['main']

        # swap hov with a lane in mainline
        if neighbor_ml_id is not None:
            num_lanes = df_group_id['Lanes'][neighbor_ml_id]

            # get the lane number of the mainline to be swapped with
            if num_lanes > 1:
                # get random lane
                lane_num = np.random.randint(low=1,
                                             high=num_lanes,
                                             size=1)[0]
            else:
                lane_num = 1

            df_merge.loc[df_merge.ID == _id, 'swapped_lane_num'] = lane_num

            lane_cols = ['Lane {} Flow'.format(lane_num),
                         'Lane {} Occupancy'.format(lane_num)]
            total_cols = ['Flow', 'Occupancy']

            # update total Flow of the mainline # TODO hov > 1 lanes, Fix else
            df_merge.loc[df_merge.ID == neighbor_ml_id, 'Flow'] = \
                df_merge.loc[df_merge.ID == neighbor_ml_id, 'Flow'].values + \
                df_merge.loc[df_merge.ID == _id, 'Flow'].values - \
                df_merge.loc[df_merge.ID == neighbor_ml_id, lane_cols[0]].values

            # update total Occupancy of the mainline
            df_merge.loc[df_merge.ID == neighbor_ml_id, 'Occupancy'] = \
                df_merge.loc[df_merge.ID == neighbor_ml_id, 'Occupancy'].values \
                + (df_merge.loc[df_merge.ID == _id, 'Occupancy'].values -
                   df_merge.loc[df_merge.ID == neighbor_ml_id, lane_cols[
                       1]].values) / num_lanes

            # swap Flow of hov with the lane of mainline
            df_merge.loc[df_merge.ID == _id, 'Flow'], \
            df_merge.loc[df_merge.ID == neighbor_ml_id, lane_cols[0]] = \
                df_merge.loc[
                    df_merge.ID == neighbor_ml_id, lane_cols[0]].values, \
                df_merge.loc[df_merge.ID == _id, 'Flow'].values

            # swap Occupancy of hov with the lane of mainline
            df_merge.loc[df_merge.ID == _id, 'Occupancy'], \
            df_merge.loc[df_merge.ID == neighbor_ml_id, lane_cols[1]] = \
                df_merge.loc[
                    df_merge.ID == neighbor_ml_id, lane_cols[1]].values, \
                df_merge.loc[df_merge.ID == _id, 'Occupancy'].values

    return df_merge


def split_data(data, test_size=0.2):
    """Splits data to training, validation and testing parts

    Note: data is not shuffled to keep the time series for plotting
    acceleration profiles

    Parameters:
    ----------
    data : pandas.Dataframe
        pandas dataframe object of the preprocessed data
    test_size : float
        portion of the data used as test data

    Returns:
    -------
    df_train : pandas.Dataframe
        pandas dataframe object containing training dataset
    df_test : pandas.Dataframe
        pandas dataframe object containing test dataset
    """
    n = int(len(data) * (1 - test_size))
    df_train, df_test = data.iloc[:n], data.iloc[n:]
    return df_train, df_test

