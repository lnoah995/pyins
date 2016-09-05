from numpy.testing import (assert_allclose, run_module_suite, assert_equal,
                           assert_)
import numpy as np
import pandas as pd
from pyins.filt import InertialSensor, LatLonObs, VeVnObs
from pyins import earth


def test_InertialSensor():
    s = InertialSensor()
    assert_equal(s.n_states, 0)
    assert_equal(s.n_noises, 0)
    assert_equal(len(s.states), 0)
    assert_equal(s.P.shape, (0, 0))
    assert_equal(s.q.shape, (0,))
    assert_equal(s.F.shape, (0, 0))
    assert_equal(s.G.shape, (0, 0))
    assert_equal(s.output_matrix().shape, (3, 0))

    s = InertialSensor(bias=0.1, bias_walk=0.2)
    assert_equal(s.n_states, 3)
    assert_equal(s.n_noises, 3)
    assert_equal(list(s.states.keys()), ['BIAS_1', 'BIAS_2', 'BIAS_3'])
    assert_equal(list(s.states.values()), [0, 1, 2])
    assert_allclose(s.P, 0.01 * np.identity(3))
    assert_equal(s.q, [0.2, 0.2, 0.2])
    assert_equal(s.F, np.zeros((3, 3)))
    assert_equal(s.G, np.identity(3))
    assert_equal(s.output_matrix(), np.identity(3))

    s = InertialSensor(scale=0.2, scale_walk=0.3)
    assert_equal(s.n_states, 3)
    assert_equal(s.n_noises, 3)
    assert_equal(list(s.states.keys()), ['SCALE_1', 'SCALE_2', 'SCALE_3'])
    assert_equal(list(s.states.values()), [0, 1, 2])
    assert_allclose(s.P, 0.04 * np.identity(3))
    assert_equal(s.q, [0.3, 0.3, 0.3])
    assert_equal(s.F, np.zeros((3, 3)))
    assert_equal(s.G, np.identity(3))
    assert_equal(s.output_matrix([1, 2, 3]), np.diag([1, 2, 3]))
    assert_equal(s.output_matrix([[1, -2, 2], [0.1, 2, 0.5]]),
                 np.array((np.diag([1, -2, 2]), np.diag([0.1, 2, 0.5]))))

    s = InertialSensor(corr_sd=0.1, corr_time=5)
    assert_equal(s.n_states, 3)
    assert_equal(s.n_noises, 3)
    assert_equal(list(s.states.keys()), ['CORR_1', 'CORR_2', 'CORR_3'])
    assert_equal(list(s.states.values()), [0, 1, 2])
    assert_allclose(s.P, 0.01 * np.identity(3))
    q = 0.1 * (2 / 5) ** 0.5
    assert_equal(s.q, [q, q, q])
    assert_allclose(s.F, -np.identity(3) / 5)
    assert_equal(s.G, np.identity(3))

    s = InertialSensor(bias=0.1, bias_walk=0.2, scale=0.3, scale_walk=0.4,
                       corr_sd=0.5, corr_time=10)
    assert_equal(s.n_states, 9)
    assert_equal(s.n_noises, 9)
    assert_equal(list(s.states.keys()),
                 ['BIAS_1', 'BIAS_2', 'BIAS_3', 'SCALE_1', 'SCALE_2',
                  'SCALE_3', 'CORR_1', 'CORR_2', 'CORR_3'])
    assert_equal(list(s.states.values()), np.arange(9))
    assert_allclose(s.P, np.diag([0.01, 0.01, 0.01, 0.09, 0.09, 0.09,
                                  0.25, 0.25, 0.25]))
    q_corr = 0.5 * (2 / 10) ** 0.5
    assert_equal(s.q, [0.2, 0.2, 0.2, 0.4, 0.4, 0.4, q_corr, q_corr, q_corr])
    assert_allclose(s.F, np.diag([0, 0, 0, 0, 0, 0, -1/10, -1/10, -1/10]))
    assert_equal(s.G, np.identity(9))

    H = s.output_matrix([1, 2, 3])
    assert_allclose(H, [[1, 0, 0, 1, 0, 0, 1, 0, 0],
                        [0, 1, 0, 0, 2, 0, 0, 1, 0],
                        [0, 0, 1, 0, 0, 3, 0, 0, 1]])

    H = s.output_matrix([[1, 2, 3], [-1, 2, 0.5]])
    assert_allclose(H[0], [[1, 0, 0, 1, 0, 0, 1, 0, 0],
                           [0, 1, 0, 0, 2, 0, 0, 1, 0],
                           [0, 0, 1, 0, 0, 3, 0, 0, 1]])
    assert_allclose(H[1], [[1, 0, 0, -1, 0, 0, 1, 0, 0],
                           [0, 1, 0, 0, 2, 0, 0, 1, 0],
                           [0, 0, 1, 0, 0, 0.5, 0, 0, 1]])


def test_LatLonObs():
    traj_point = pd.Series(data={
        'lat': 40,
        'lon': 30,
        'VE': 4,
        'VN': -3,
        'h': 15,
        'p': 0,
        'r': 0
    })
    obs_data = pd.DataFrame(index=[50])
    obs_data['lat'] = [40.0001]
    obs_data['lon'] = [30.0002]
    obs = LatLonObs(obs_data, 10)

    ret = obs.compute_obs(55, traj_point)
    assert_(ret is None)

    z, H, R = obs.compute_obs(50, traj_point)
    z_true = [np.deg2rad(-0.0002) * earth.R0 * np.cos(np.deg2rad(40)),
              np.deg2rad(-0.0001) * earth.R0]
    assert_allclose(z, z_true, rtol=1e-5)

    assert_allclose(H, [[1, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 0, 0, 0]])

    assert_allclose(R, [[100, 0], [0, 100]])


def test_VeVnObs():
    traj_point = pd.Series(data={
        'lat': 40,
        'lon': 30,
        'VE': 4,
        'VN': -3,
        'h': 15,
        'p': 0,
        'r': 0
    })
    obs_data = pd.DataFrame(index=[50])
    obs_data['VE'] = [3]
    obs_data['VN'] = [-2]
    obs = VeVnObs(obs_data, 10)

    ret = obs.compute_obs(55, traj_point)
    assert_(ret is None)

    z, H, R = obs.compute_obs(50, traj_point)
    assert_allclose(z, [1, -1])
    assert_allclose(H, [[0, 0, 1, 0, 0, 0, -2],
                        [0, 0, 0, 1, 0, 0, -3]])


if __name__ == '__main__':
    run_module_suite()
