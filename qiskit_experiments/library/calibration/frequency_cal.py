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

"""Ramsey XY frequency calibration experiment."""

from typing import List, Optional

from qiskit.providers.backend import Backend

from qiskit_experiments.framework import ExperimentData
from qiskit_experiments.library.characterization.ramsey_xy import RamseyXY
from qiskit_experiments.calibration_management.backend_calibrations import BackendCalibrations
from qiskit_experiments.calibration_management.update_library import BaseUpdater
from qiskit_experiments.calibration_management.base_calibration_experiment import (
    BaseCalibrationExperiment,
)


class FrequencyCal(BaseCalibrationExperiment, RamseyXY):
    """A qubit frequency calibration experiment based on the Ramsey XY experiment.

    # section: see_also
        qiskit_experiments.library.characterization.ramsey_xy.RamseyXY
    """

    def __init__(
        self,
        qubit: int,
        calibrations: BackendCalibrations,
        backend: Optional[Backend] = None,
        delays: Optional[List] = None,
        unit: str = "s",
        osc_freq: float = 2e6,
        auto_update: bool = True,
    ):
        """
        Args:
            qubit: The qubit on which to run the frequency calibration.
            calibrations: The calibrations instance with the schedules.
            backend: Optional, the backend to run the experiment on.
            delays: The list of delays that will be scanned in the experiment.
            unit: The unit of the delays. Accepted values are dt, i.e. the
                duration of a single sample on the backend, seconds, and sub-units,
                e.g. ms, us, ns.
            osc_freq: A frequency shift in Hz that will be applied by means of
                a virtual Z rotation to increase the frequency of the measured oscillation.
            auto_update: If set to True, which is the default, then the experiment will
                automatically update the frequency in the calibrations.
        """
        super().__init__(
            calibrations,
            qubit,
            backend=backend,
            delays=delays,
            unit=unit,
            osc_freq=osc_freq,
            cal_parameter_name="qubit_lo_freq",
            auto_update=auto_update,
        )

        # Instruction schedule map to bring in the calibrations for the sx gate.
        self.set_transpile_options(inst_map=calibrations.default_inst_map)

    def _add_cal_metadata(self, experiment_data: ExperimentData):
        """Add the oscillation frequency of the experiment to the metadata."""

        param_val = self._cals.get_parameter_value(
            self._param_name,
            self.physical_qubits,
            group=self.experiment_options.group,
        )

        experiment_data.metadata["cal_param_value"] = param_val
        experiment_data.metadata["cal_group"] = self.experiment_options.group
        experiment_data.metadata["osc_freq"] = self.experiment_options.osc_freq

    def update_calibrations(self, experiment_data: ExperimentData):
        """Update the frequency using the reported frequency less the imparted oscillation."""

        result_index = self.experiment_options.result_index
        osc_freq = experiment_data.metadata["osc_freq"]
        group = experiment_data.metadata["cal_group"]
        old_freq = experiment_data.metadata["cal_param_value"]

        fit_freq = BaseUpdater.get_value(experiment_data, "freq", result_index)
        new_freq = old_freq + fit_freq - osc_freq

        BaseUpdater.add_parameter_value(
            self._cals,
            experiment_data,
            new_freq,
            self._param_name,
            group=group,
        )
