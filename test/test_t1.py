# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
Test T1 experiment
"""

from test.base import QiskitExperimentsTestCase
from qiskit_experiments.framework import ExperimentData, ParallelExperiment
from qiskit_experiments.library import T1
from qiskit_experiments.library.characterization import T1Analysis
from qiskit_experiments.test.t1_backend import T1Backend


class TestT1(QiskitExperimentsTestCase):
    """
    Test measurement of T1
    """

    def test_t1_end2end(self):
        """
        Test T1 experiment using a simulator.
        """

        dt_factor = 2e-7

        t1 = 25e-6
        backend = T1Backend(
            [t1],
            initial_prob1=[0.02],
            readout0to1=[0.02],
            readout1to0=[0.02],
            dt_factor=dt_factor,
        )

        delays = list(
            range(
                int(1e-6 / dt_factor),
                int(40e-6 / dt_factor),
                int(3e-6 / dt_factor),
            )
        )

        exp = T1(0, delays, unit="dt")
        exp.set_analysis_options(p0={"amp": 1, "tau": t1 / dt_factor, "base": 0})
        exp_data = exp.run(backend, shots=10000)
        exp_data.block_for_results()  # Wait for analysis to finish.
        res = exp_data.analysis_results("T1")
        fitval = res.value
        self.assertEqual(res.quality, "good")
        self.assertAlmostEqual(fitval.value, t1, delta=3)
        self.assertEqual(fitval.unit, "s")

    def test_t1_parallel(self):
        """
        Test parallel experiments of T1 using a simulator.
        """

        t1 = [25, 15]
        delays = list(range(1, 40, 3))

        exp0 = T1(0, delays)
        exp2 = T1(2, delays)
        par_exp = ParallelExperiment([exp0, exp2])
        res = par_exp.run(T1Backend([t1[0], None, t1[1]]))
        res.block_for_results()

        for i in range(2):
            sub_res = res.child_data(i).analysis_results("T1")
            self.assertEqual(sub_res.quality, "good")
            self.assertAlmostEqual(sub_res.value.value, t1[i], delta=3)

    def test_t1_parallel_different_analysis_options(self):
        """
        Test parallel experiments of T1 using a simulator, for the case where
        the sub-experiments have different analysis options
        """

        t1 = 25
        delays = list(range(1, 40, 3))

        exp0 = T1(0, delays)
        exp0.set_analysis_options(p0={"tau": 30})
        exp1 = T1(1, delays)
        exp1.set_analysis_options(p0={"tau": 1000000})

        par_exp = ParallelExperiment([exp0, exp1])
        res = par_exp.run(T1Backend([t1, t1]))
        res.block_for_results()

        sub_res = []
        for i in range(2):
            sub_res.append(res.child_data(i).analysis_results("T1"))

        self.assertEqual(sub_res[0].quality, "good")
        self.assertAlmostEqual(sub_res[0].value.value, t1, delta=3)
        self.assertEqual(sub_res[1].quality, "bad")

    def test_t1_analysis(self):
        """
        Test T1Analysis
        """

        data = ExperimentData()
        data._metadata = {
            "job_metadata": [
                {
                    "run_options": {"meas_level": 2},
                    # TODO remove this, issue #456
                    "experiment_options": {"conversion_factor": 1, "unit": "s"},
                },
            ]
        }

        numbers = [750, 1800, 2750, 3550, 4250, 4850, 5450, 5900, 6400, 6800, 7000, 7350, 7700]

        for i, count0 in enumerate(numbers):
            data.add_data(
                {
                    "counts": {"0": count0, "1": 10000 - count0},
                    "metadata": {
                        "xval": (3 * i + 1) * 1e-9,
                        "experiment_type": "T1",
                        "qubit": 0,
                        "unit": "s",
                    },
                }
            )

        res = T1Analysis()._run_analysis(data)[0][1]
        self.assertEqual(res.quality, "good")
        self.assertAlmostEqual(res.value.value, 25e-9, delta=3)

    def test_t1_metadata(self):
        """
        Test the circuits metadata
        """

        delays = list(range(1, 40, 3))
        exp = T1(0, delays, unit="ms")

        # TODO remove this, issue #456
        exp.set_experiment_options(conversion_factor=1 / 1000)

        circs = exp.circuits()

        self.assertEqual(len(circs), len(delays))

        for delay, circ in zip(delays, circs):
            self.assertEqual(
                circ.metadata,
                {
                    "experiment_type": "T1",
                    "qubit": 0,
                    "xval": delay / 1000,
                    "unit": "s",
                },
            )

    def test_t1_low_quality(self):
        """
        A test where the fit's quality will be low
        """

        data = ExperimentData()
        data._metadata = {
            "job_metadata": [
                {
                    "run_options": {"meas_level": 2},
                    # TODO remove this, issue #456
                    "experiment_options": {"conversion_factor": 1, "unit": "s"},
                },
            ]
        }

        for i in range(10):
            data.add_data(
                {
                    "counts": {"0": 10, "1": 10},
                    "metadata": {
                        "xval": i * 1e-9,
                        "experiment_type": "T1",
                        "qubit": 0,
                        "unit": "s",
                    },
                }
            )

        res = T1Analysis()._run_analysis(data)[0][1]
        self.assertEqual(res.quality, "bad")

    def test_experiment_config(self):
        """Test converting to and from config works"""
        exp = T1(0, [1, 2, 3, 4, 5], unit="s")
        loaded_exp = T1.from_config(exp.config)
        self.assertNotEqual(exp, loaded_exp)
        self.assertTrue(self.experiments_equiv(exp, loaded_exp))

    def test_roundtrip_serializable(self):
        """Test round trip JSON serialization"""
        exp = T1(0, [1, 2, 3, 4, 5], unit="s")
        self.assertRoundTripSerializable(exp, self.experiments_equiv)
