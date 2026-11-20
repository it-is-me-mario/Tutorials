ISTAT supply-use data for CVXLab
================================

This directory contains the CVXLab model configuration, classified English
sets and 2022 ISTAT input data. Execute the MARIO notebook to regenerate
the sets and input tables using ``to_cvxlab``. The exported files are ready
for loading into the CVXLab model.

model_settings.xlsx SHA-256:
40aa3c9df67ebfd0e13917dd9a00419743cddfa9a80a6b5862dff3826895263f

Input tables: make_0, use_0, imports_0, extensions_0, total_activity_0 and
total_demand_0. The file also contains blank delta_make, delta_use and
delta_imports templates. These are CVXLab scenario inputs, not mapped MARIO
matrices; the model's blank_fill=0 supplies their zeros at loading time.
Reference is the zero-change scenario label in sets.xlsx. The exported
values come from the MARIO database's baseline scenario.

``model_settings.xlsx`` defines the input tables, set coordinates, variable
filters and equations. The configuration has no exogenous VY input; this
final-demand accounting block remains in the MARIO database.

Products and activities: 15 each. Final demand: 7 categories. Extensions: 8
income/accounting rows and 2 satellite accounts. Monetary values remain in
million EUR; the satellite accounts are total employment in persons and net domestic
energy use in TJ. All eight income/accounting rows are retained.

The source is ISTAT's 2020–2022 edition, observation year 2022, with
employment and PEFA observations from Eurostat for 2022. English translations
and aggregation are modifications for this example, not official source
revisions.

Source attribution and reuse
----------------------------

* ISTAT: https://www.istat.it/tavole-di-dati/il-sistema-di-tavole-input-output-anni-2020-2022/
* ISTAT CC BY 4.0 notice: https://www.istat.it/note-legali/
* Eurostat employment: https://doi.org/10.2908/nama_10_a64_e
* Eurostat PEFA: https://doi.org/10.2908/env_ac_pefa04
* Eurostat access date: 20 November 2026.
* Eurostat reuse: https://ec.europa.eu/eurostat/help/copyright-notice
* Model configuration source: https://github.com/cvxlab/cvxlab/tree/466b50c2c5ad8b4b2a7f02f71da5f473decbc81d/docs/source/tutorials/input_output_analysis_mario

The accompanying Apache 2.0 LICENSE for the receiving configuration is retained.
Keep data-source acknowledgements and the description of modifications with
the derived input package.
