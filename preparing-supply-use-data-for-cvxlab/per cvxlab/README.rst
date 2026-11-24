ISTAT supply-use data for CVXLab
================================

This directory contains the receiving model settings, final classified sets
and regenerated inputs for Italy's 2022 supply-use database. Run
``preparing_supply_use_data_for_cvxlab.ipynb`` from the parent folder.
The notebook ends at ``to_cvxlab`` and uses this ``per cvxlab`` directory.

The sets contain 15 products, 15 activities, 7 final-demand categories,
all 8 value-added/accounting rows and 3 satellites:

* Greenhouse gases (CO2 equivalent) [AEA: GHG], in tonnes CO2 equivalent.
* Total employment (domestic concept), in persons.
* Net domestic energy use, in TJ.

The classified member order, nullable type filters, reporting groups and
four scenarios are retained: reference, domestic_energy,
petroleum_free_transport and mixed. Only the electricity/gas activity and
product are classified as power. Blank type cells intentionally leave other
members outside that filter.

Reference input tables are make_0, use_0, imports_0, extensions_0,
total_activity_0 and total_demand_0. extensions_0 contains 186 rows:
8 value-added accounts by 15 activities, plus 3 satellites by
15 activities and 7 final-demand categories. The receiving configuration
has no exogenous VY input; that matrix remains in MARIO.

The delta_use and delta_imports templates cover all four CVXLab scenarios;
delta_extensions has no scenario dimension in this configuration. Their
values are deliberately blank: they are not mapped to MARIO matrices.
CVXLab applies the declared blank_fill=0 during loading. Scenario shocks
must be supplied by the receiving analysis. An export report can list these
unmapped blank inputs and the intentionally blank type attributes.

All monetary values are in million EUR without numerical rescaling.
The settings' equations, variables, filters and table definitions are
preserved. Supplied model_settings.xlsx SHA-256:
334732aed17f81f7091a58708c7b56ddca02fd475d64733989a0aecf1ab84c3d

Source attribution and reuse
----------------------------

* ISTAT 2020-2022 edition, observation year 2022:
  https://www.istat.it/tavole-di-dati/il-sistema-di-tavole-input-output-anni-2020-2022/
* ISTAT reuse: https://www.istat.it/note-legali/
* Eurostat air emissions accounts: https://doi.org/10.2908/env_ac_ainah_r2
* Eurostat employment: https://doi.org/10.2908/nama_10_a64_e
* Eurostat PEFA: https://doi.org/10.2908/env_ac_pefa04
* Eurostat observations: Italy, 2022. Access date: 24 November 2026.
* Eurostat reuse: https://ec.europa.eu/eurostat/help/copyright-notice
* Receiving configuration adapted from:
  https://github.com/cvxlab/cvxlab/tree/466b50c2c5ad8b4b2a7f02f71da5f473decbc81d/docs/source/tutorials/input_output_analysis_mario

The example aggregates productive classifications and translates labels;
these are modifications for this example, not official source revisions.
Retain this source acknowledgement and the accompanying Apache 2.0 LICENSE.
The source cache is downloaded separately and stays outside the repository.
