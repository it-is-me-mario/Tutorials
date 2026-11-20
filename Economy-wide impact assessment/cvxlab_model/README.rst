ISTAT supply-use data for CVXLab
================================

This directory contains the CVXLab model configuration, classified English
sets and 2022 ISTAT reference inputs. Execute the MARIO notebook to regenerate
the sets and input tables using ``to_cvxlab``. The exported files are ready
for loading into the CVXLab model.

model_settings.xlsx SHA-256:
6fd98098db6bb27dafef7414c09fbeaa037b4071990b43441546bc4cd8ad05aa

Reference tables: make_0, use_0, imports_0, extensions_0, total_activity_0 and
total_demand_0. The file also contains blank delta_make, delta_use and
delta_imports templates for Reference. The model's declared blank_fill=0
supplies their zero values when loading into CVXLab SQLite.

``model_settings.xlsx`` defines the input tables, set coordinates, variable
filters and equations. The configuration has no exogenous VY input; this
final-demand accounting block remains in the MARIO database.

Products and activities: 15 each. Final demand: 7 categories. Extensions: 8
income/accounting rows and 27 satellite accounts. Monetary values remain in
million EUR; satellite units are t, t CO2-eq, t SO2-eq, t NMVOC-eq, persons,
hours and TJ according to the row described in the notebook.

The source is ISTAT's 2020–2022 edition, observation year 2022, with AEA,
employment and PEFA observations from Eurostat for 2022. English translations
and aggregation are modifications for this example, not official source
revisions.

Source attribution and reuse
----------------------------

* ISTAT: https://www.istat.it/tavole-di-dati/il-sistema-di-tavole-input-output-anni-2020-2022/
* ISTAT CC BY 4.0 notice: https://www.istat.it/note-legali/
* Eurostat AEA: https://doi.org/10.2908/env_ac_ainah_r2
* Eurostat employment: https://doi.org/10.2908/nama_10_a64_e
* Eurostat PEFA: https://doi.org/10.2908/env_ac_pefa04
* Eurostat access date: 20 November 2026.
* Eurostat reuse: https://ec.europa.eu/eurostat/help/copyright-notice
* Model configuration source: https://github.com/cvxlab/cvxlab/tree/466b50c2c5ad8b4b2a7f02f71da5f473decbc81d/docs/source/tutorials/input_output_analysis_mario

The accompanying Apache 2.0 LICENSE for the receiving configuration is retained.
Keep data-source acknowledgements and the description of modifications with
the derived input package.
