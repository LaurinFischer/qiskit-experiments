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

"""Half angle characterization."""

from typing import List, Optional
import numpy as np

from qiskit import QuantumCircuit
from qiskit.providers import Backend

from qiskit_experiments.framework import BaseExperiment, Options
from qiskit_experiments.library.characterization.analysis import FineHalfAngleAnalysis
from qiskit_experiments.curve_analysis import ParameterRepr


class HalfAngle(BaseExperiment):
    r"""An experiment class to measure the amount by which sx and x are not parallel.

    # section: overview

        This experiment runs circuits that repeat blocks of :code:`sx - sx - y` gates
        inserted in a Ramsey type experiment, i.e. the full gate sequence is thus
        :code:`Ry(π/2) - [sx - sx - y] ^ n - sx` where :code:`n` is varied.

        .. parsed-literal::

                    ┌─────────┐┌────┐┌────┐┌───┐   ┌────┐┌────┐┌───┐┌────┐ ░ ┌─┐
               q_0: ┤ Ry(π/2) ├┤ sx ├┤ sx ├┤ y ├...┤ sx ├┤ sx ├┤ y ├┤ sx ├─░─┤M├
                    └─────────┘└────┘└────┘└───┘   └────┘└────┘└───┘└────┘ ░ └╥┘
            meas: 1/════════════════════════════...═══════════════════════════╩═
                                                                              0

        This sequence measures angle errors where the axis of the :code:`sx` and :code:`x`
        rotation are not parallel. A similar experiment is described in Ref.~[1] where the
        gate sequence :code:`x - y` is repeated to amplify errors caused by non-orthogonal
        :code:`x` and :code:`y` rotation axes. Such errors can occur due to phase errors.
        For example, the non-linearities in the mixer's skew for :math:`\pi/2` pulses may
        be different from the :math:`\pi` pulse.

    # section: reference
        .. ref_arxiv:: 1 1504.06597
    """

    __analysis_class__ = FineHalfAngleAnalysis

    @classmethod
    def _default_experiment_options(cls) -> Options:
        r"""Default values for the half angle experiment.

        Experiment Options:
            repetitions (List[int]): A list of the number of times that the gate
                sequence :code:`[sx sx y]` is repeated.
        """
        options = super()._default_experiment_options()
        options.repetitions = list(range(15))
        return options

    @classmethod
    def _default_transpile_options(cls) -> Options:
        """Default transpile options.

        The basis gates option should not be changed since it will affect the gates and
        the pulses that are run on the hardware.
        """
        options = super()._default_transpile_options()
        options.basis_gates = ["sx", "rz", "y"]
        options.inst_map = None
        return options

    @classmethod
    def _default_analysis_options(cls) -> Options:
        r"""Default analysis options.

        If the rotation error is very small the fit may chose a d_theta close to
        :math:`\pm\pi`. To prevent this we impose bounds on d_theta. Note that the
        options angle per gate, phase offset and amp are not intended to be changed.
        """
        options = super()._default_analysis_options()
        options.result_parameters = [ParameterRepr("d_theta", "d_hac", "rad")]
        options.normalization = True
        options.angle_per_gate = np.pi
        options.phase_offset = -np.pi / 2
        options.amp = 1.0
        options.bounds.update({"d_theta": (-np.pi / 2, np.pi / 2)})

        return options

    def __init__(self, qubit: int, backend: Optional[Backend] = None):
        """Setup a half angle experiment on the given qubit.

        Args:
            qubit: The qubit on which to run the fine amplitude calibration experiment.
            backend: Optional, the backend to run the experiment on.
        """
        super().__init__([qubit], backend=backend)

    @staticmethod
    def _pre_circuit() -> QuantumCircuit:
        """Return the preparation circuit for the experiment."""
        return QuantumCircuit(1)

    def circuits(self) -> List[QuantumCircuit]:
        """Create the circuits for the half angle calibration experiment."""

        circuits = []

        for repetition in self.experiment_options.repetitions:
            circuit = self._pre_circuit()

            # First ry gate
            circuit.rz(np.pi / 2, 0)
            circuit.sx(0)
            circuit.rz(-np.pi / 2, 0)

            # Error amplifying sequence
            for _ in range(repetition):
                circuit.sx(0)
                circuit.sx(0)
                circuit.y(0)

            circuit.sx(0)
            circuit.measure_all()

            circuit.metadata = {
                "experiment_type": self._type,
                "qubits": self.physical_qubits,
                "xval": repetition,
                "unit": "repetition number",
            }

            circuits.append(circuit)

        return circuits
