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
T1 Analysis class.
"""
from typing import Union, List

import qiskit_experiments.curve_analysis as curve

from qiskit_experiments.framework import Options


class T1Analysis(curve.DecayAnalysis):
    r"""A class to analyze T1 experiments.

    # section: see_also
        qiskit_experiments.curve_analysis.standard_analysis.decay.DecayAnalysis

    """

    @classmethod
    def _default_options(cls) -> Options:
        """Default analysis options."""
        options = super()._default_options()
        options.xlabel = "Delay"
        options.ylabel = "P(1)"
        options.xval_unit = "s"
        options.result_parameters = [curve.ParameterRepr("tau", "T1", "s")]

        return options

    def _generate_fit_guesses(
        self, user_opt: curve.FitOptions
    ) -> Union[curve.FitOptions, List[curve.FitOptions]]:
        """Apply conversion factor to tau."""
        conversion_factor = self._experiment_options()["conversion_factor"]

        if user_opt.p0["tau"] is not None:
            user_opt.p0["tau"] *= conversion_factor

        return super()._generate_fit_guesses(user_opt)

    def _evaluate_quality(self, fit_data: curve.FitData) -> Union[str, None]:
        """Algorithmic criteria for whether the fit is good or bad.

        A good fit has:
            - a reduced chi-squared lower than three
            - absolute amp is within [0.9, 1.1]
            - base is less than 0.1
            - amp error is less than 0.1
            - tau error is less than its value
            - base error is less than 0.1
        """
        amp = fit_data.fitval("amp")
        tau = fit_data.fitval("tau")
        base = fit_data.fitval("base")

        criteria = [
            fit_data.reduced_chisq < 3,
            abs(amp.value - 1.0) < 0.1,
            abs(base.value) < 0.1,
            amp.stderr is None or amp.stderr < 0.1,
            tau.stderr is None or tau.stderr < tau.value,
            base.stderr is None or base.stderr < 0.1,
        ]

        if all(criteria):
            return "good"

        return "bad"
