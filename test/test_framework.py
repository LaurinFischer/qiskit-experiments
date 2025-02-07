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

"""Tests for base experiment framework."""

from test.fake_backend import FakeBackend
from test.fake_experiment import FakeExperiment, FakeAnalysis
from test.base import QiskitExperimentsTestCase
import ddt

from qiskit import QuantumCircuit
from qiskit_experiments.framework import ExperimentData


@ddt.ddt
class TestFramework(QiskitExperimentsTestCase):
    """Test Base Experiment"""

    @ddt.data(None, 1, 2, 3)
    def test_job_splitting(self, max_experiments):
        """Test job splitting"""

        num_circuits = 10
        backend = FakeBackend(max_experiments=max_experiments)

        class Experiment(FakeExperiment):
            """Fake Experiment to test job splitting"""

            def circuits(self):
                """Generate fake circuits"""
                qc = QuantumCircuit(1)
                qc.measure_all()
                return num_circuits * [qc]

        exp = Experiment([0])
        expdata = exp.run(backend)
        job_ids = expdata.job_ids

        # Comptue expected number of jobs
        if max_experiments is None:
            num_jobs = 1
        else:
            num_jobs = num_circuits // max_experiments
            if num_circuits % max_experiments:
                num_jobs += 1
        self.assertEqual(len(job_ids), num_jobs)

    def test_analysis_replace_results_true(self):
        """Test running analysis with replace_results=True"""
        analysis = FakeAnalysis()
        expdata1 = analysis.run(ExperimentData(), seed=54321).block_for_results()
        result_ids = [res.result_id for res in expdata1.analysis_results()]
        expdata2 = analysis.run(expdata1, replace_results=True, seed=12345).block_for_results()

        self.assertEqual(expdata1, expdata2)
        self.assertEqual(expdata1.analysis_results(), expdata2.analysis_results())
        self.assertEqual(result_ids, list(expdata2._deleted_analysis_results))

    def test_analysis_replace_results_false(self):
        """Test running analysis with replace_results=False"""
        analysis = FakeAnalysis()
        expdata1 = analysis.run(ExperimentData(), seed=54321).block_for_results()
        expdata2 = analysis.run(expdata1, replace_results=False, seed=12345).block_for_results()

        self.assertNotEqual(expdata1, expdata2)
        self.assertNotEqual(expdata1.experiment_id, expdata2.experiment_id)
        self.assertNotEqual(expdata1.analysis_results(), expdata2.analysis_results())
