CVXLab inputs for the Italian reference
=======================================

``model_settings.xlsx`` is the configuration from the CVXLab economy-wide
impact-assessment tutorial at revision
``466b50c2c5ad8b4b2a7f02f71da5f473decbc81d``. Its original Apache-2.0 licence
is included. The configuration uses combined make, use, import and extension
tables as described in that tutorial.

``sets.xlsx`` contains 18 products, 29 intermediate activities, 9 final-demand
categories, 12 factors and one GHG indicator. Electricity and the twelve native
generation technologies have type ``power``. Other members have type ``other``.
The medium reporting aggregation retains the prepared reference labels.
The high reporting aggregation uses the five groups in ``Aggregation II``
from ``aggregation.xlsx`` for products and production activities.
The three scenarios are Reference, High_RES and High_RES_domestic.

``input_data/input_data.xlsx`` contains reference flows populated through
MARIO's ``to_cvxlab`` API, using the corrected reference.
``total_activity_0`` keeps its coordinates but its values are intentionally blank
in this published package. Run the notebook's local ``to_cvxlab`` export to fill
all six reference tables, including the activity outputs required by CVXLab.
Its three delta tables contain the corresponding
market-share, use and import shocks for the scenario assumptions in the notebook.
The API refreshes reference values and preserves those scenario tables.
Its report lists the delta tables as unmapped because the configuration supplies
them separately.

Reference monetary values are EUR and GHG values are kg CO2-equivalent.
Market-share and intermediate-input coefficient shocks are dimensionless.
Final-demand and final-import shocks are EUR. The combined extensions table
retains the zero entries for final-demand factors required by CVXLab's domain.

Zero-output normalization
-------------------------

The original configuration calculates coefficients with ``minv(diag(X_0))``
and ``minv(diag(Q_0))``. The Italian reference contains zero-output activities
for nuclear and tide/wave generation. ``diag(X_0)`` is singular, so the original model
requires zero-safe normalization before it can solve this reference.
The reference flows and scenario shocks are checked against MARIO.
Run the local export to populate ``total_activity_0`` before using the model.

Sources and licences
--------------------

* Original configuration https://github.com/cvxlab/cvxlab/tree/466b50c2c5ad8b4b2a7f02f71da5f473decbc81d/docs/source/tutorials/input_output_analysis_mario
* EXIOBASE 3.8.2 https://doi.org/10.5281/zenodo.5589597
* EXIOBASE attribution https://doi.org/10.1111/jiec.12715

Economic source data and classifications from EXIOBASE 3.8.2 retain CC-BY-SA-4.0.
The direct electricity-emission correction uses the public 3.11.2 ixi IOT
for 2022, with the same AR6 GWP100 combustion profile as the SUT.
Its source conditions are available at
https://zenodo.org/records/23039074/files/LICENSE.txt?download=1.
Retain these source notices and the accompanying configuration licence.
