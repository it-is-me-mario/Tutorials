ISTAT supply-use data for CVXLab
================================

This directory contains the CVXLab model configuration, classified English
sets and 2022 ISTAT input data. Execute the MARIO notebook to regenerate
the sets and input tables using ``to_cvxlab``. The exported files are ready
for loading into the CVXLab model.

Supplied model_settings.xlsx SHA-256:
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
income/accounting rows and 26 satellite accounts. Monetary values remain
in million EUR. All eight income/accounting rows are retained.

AEA includes overlapping totals and components, which must be read separately.

.. list-table:: Satellite accounts
   :header-rows: 1

   * - Indicator
     - Unit
   * - Greenhouse gases (CO2 equivalent) [AEA: GHG]
     - t CO2-eq
   * - Carbon dioxide [AEA: CO2]
     - t
   * - Methane [AEA: CH4]
     - t
   * - Methane (CO2 equivalent) [AEA: CH4_CO2E]
     - t CO2-eq
   * - Nitrous oxide [AEA: N2O]
     - t
   * - Nitrous oxide (CO2 equivalent) [AEA: N2O_CO2E]
     - t CO2-eq
   * - Hydrofluorocarbones (CO2 equivalent) [AEA: HFC_CO2E]
     - t CO2-eq
   * - Perfluorocarbones (CO2 equivalent) [AEA: PFC_CO2E]
     - t CO2-eq
   * - Nitrogen trifluoride and sulphur hexafluoride (CO2 equivalent) [AEA: NF3_SF6_CO2E]
     - t CO2-eq
   * - Carbon dioxide from biomass used as a fuel [AEA: CO2_BIO]
     - t
   * - Acidifying gases (SO2 equivalent) [AEA: ACG]
     - t SO2-eq
   * - Sulphur oxides (SO2 equivalent) [AEA: SOX_SO2E]
     - t SO2-eq
   * - Nitrogen oxides (SO2 equivalent) [AEA: NOX_SO2E]
     - t SO2-eq
   * - Ammonia (SO2 equivalent) [AEA: NH3_SO2E]
     - t SO2-eq
   * - Ozone precursors (NMVOC equivalent) [AEA: O3PR]
     - t NMVOC-eq
   * - Nitrogen oxides (NMVOC equivalent) [AEA: NOX_NMVOCE]
     - t NMVOC-eq
   * - Carbon monoxide [AEA: CO]
     - t
   * - Carbon monoxide (NMVOC equivalent) [AEA: CO_NMVOCE]
     - t NMVOC-eq
   * - Methane (NMVOC equivalent) [AEA: CH4_NMVOCE]
     - t NMVOC-eq
   * - Nitrogen oxides [AEA: NOX]
     - t
   * - Ammonia [AEA: NH3]
     - t
   * - Particulates < 2.5µm [AEA: PM2_5]
     - t
   * - Particulates < 10µm [AEA: PM10]
     - t
   * - Non-methane volatile organic compounds [AEA: NMVOC]
     - t
   * - Total employment (domestic concept)
     - persons
   * - Net domestic energy use
     - TJ

The source is ISTAT's 2020–2022 edition, observation year 2022, with
AEA, employment and PEFA observations from Eurostat for 2022. English translations
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
