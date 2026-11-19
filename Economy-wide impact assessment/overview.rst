This tutorial studies changes to Italy's electricity supply and their effects
on value added, imports and GHG emissions. It accompanies the
`CVXLab economy-wide impact assessment tutorial <https://cvxlab.readthedocs.io/en/dev/tutorials/input_output_analysis_mario/input_output_analysis_mario.html>`_.
Both use the same Italian reference with twelve electricity-generation
technologies.

Prepare the reference below, update its electricity mix to 2022 and replace
direct electricity-emission intensities using the public EXIOBASE 3.11.2 IOT.
Then calculate the scenarios in MARIO or export it to CVXLab to formulate and solve the model there.

Familiarity with input-output analysis is assumed. MARIO's Table formats guide
introduces the accounting structures used in the exercise.
`Table formats <https://www.marioproject.com/en/latest/get_started/table_formats.html>`_.

Use a Python 3.12 Conda environment and install MARIO 1.3.5.

.. code:: bash

   python -m pip install "mariopy==1.3.5" jupyterlab

The CVXLab path uses the CVXLab revision identified in the notebook.
Installation guidance is available in
`MARIO getting started <https://www.marioproject.com/en/latest/get_started/index.html>`_
and `CVXLab installation <https://cvxlab.readthedocs.io/en/dev/installation.html>`_.

.. _problem-statement:

.. admonition:: Problem statement

   How do changes to Italy's electricity supply propagate to domestic value
   added, imports and greenhouse-gas emissions?

   Compare the **Reference** system with the two scenarios used by the CVXLab
   exercise.

   * **High_RES** assigns the High RES electricity-generation shares below.
   * **High_RES_domestic** adds domestic substitution of imported electricity
     to that mix. Imported electricity for production and final consumption is
     redirected to the domestic electricity product.

   The second comparison identifies the additional effect of electricity-import
   substitution. Fuel and other product imports follow the input requirements
   of domestic production. Both scenarios use a comparative-statics calculation.

   .. math::

      \begin{array}{lrr}
      \text{Electricity generation by...} & \text{Reference (2022)} & \text{High RES} \\
      \hline
      \text{Coal} & 8.07\% & 0.0\% \\
      \text{Gas} & 50.49\% & 0.0\% \\
      \text{Nuclear} & 0.00\% & 15.0\% \\
      \text{Hydro} & 10.14\% & 9.0\% \\
      \text{Wind} & 7.31\% & 38.0\% \\
      \text{Petroleum} & 4.61\% & 0.0\% \\
      \text{Biomass and waste} & 6.29\% & 5.0\% \\
      \text{Solar photovoltaic} & 10.04\% & 31.0\% \\
      \text{Tide, wave, ocean} & 0.00\% & 0.5\% \\
      \text{Geothermal} & 2.08\% & 1.5\% \\
      \text{Others} & 0.97\% & 0.0\% \\
      \end{array}

   These are monetary production shares within the electricity-generation
   activities. Reference values reflect the 2022 electricity-mix update applied
   below. Others combines solar thermal and the remaining electricity
   activity. Secondary electricity production by other industries retains its
   reference market share. High RES shares specify the common teaching scenario.

   Calculate each scenario's percentage change in value added, imports and GHG
   emissions relative to Reference, then compare the two High RES outcomes.

.. _environment-and-inputs:
.. _run-the-tutorial:
.. _tutorial-materials:

.. rubric:: Tutorial materials

* :download:`economy_wide_impact_assessment.ipynb <economy_wide_impact_assessment.ipynb>`
  contains the complete MARIO workflow, installation commands and optional
  CVXLab export and model-construction calls.
* :download:`aggregation.xlsx <aggregation.xlsx>` supplies the aggregation
  mapping with all twelve electricity-generation technologies retained.
* :download:`results.zip <results.zip>` contains the nine exported matrices,
  matching sets and summary for the three executed MARIO scenarios.
* :download:`scenario_summary.csv <scenario_summary.csv>` contains the executed
  MARIO comparison in M EUR and kt CO2-equivalent.
* :download:`cvxlab_model.zip <cvxlab_model.zip>` contains the CVXLab
  settings, classified sets, corrected reference flows and the three scenarios'
  shock tables. Activity output values in ``total_activity_0`` are left blank;
  ``to_cvxlab`` fills them when the notebook is executed locally.
* The `CVXLab tutorial materials <https://cvxlab.readthedocs.io/en/dev/_downloads/f16216b31c3f637ad45967d9f5ee116d/ioa_mario.zip>`_ provide its conceptual workbook
  and receiving model configuration for the optional CVXLab path.

Download the MARIO notebook, aggregation workbook and summary into one working folder. Follow the
steps below or run the notebook cells in sequence. An online version is
available as :doc:`Notebook <notebook>`.

``Xa`` and the corrected emission-intensity tables are omitted from the published
materials; the local CVXLab export still includes the activity output it needs.

The source archives are obtained in Database download. The notebook writes the
scenario matrices, ``sets.xlsx`` and an updated summary under ``results``.

.. _prepare-the-reference-system:

Database download
-----------------

Use EXIOBASE **3.8.2**, reference year **2022**, for both the monetary SUT and
its matching industry-by-industry satellite accounts. MARIO retrieves the two
archives from Zenodo and verifies their size and checksum. Valid existing
archives are reused. Keep the archives zipped for the parser.

.. code:: python

   from pathlib import Path
   import mario

   source_dir = Path("source_data")
   sut_path = source_dir / "MRSUT_2022.zip"
   iot_path = source_dir / "IOT_2022_ixi.zip"

   mario.download_exiobase3(
       path=source_dir,
       years=[2022],
       table="SUT",
       version="3.8.2",
       extract=False,
   )
   mario.download_exiobase3(
       path=source_dir,
       years=[2022],
       table="IOT",
       system="ixi",
       version="3.8.2",
       extract=False,
   )

The initial downloads total approximately 1 GB. The correction step additionally
downloads the public 3.11.2 ixi IOT for 2022 into ``source_data/3.11.2``.
The separate directory keeps identically named archives from different releases
apart. No privately supplied SUT is needed. The files can also be saved manually
in ``source_data`` from the official EXIOBASE record.
`EXIOBASE 3.8.2 <https://zenodo.org/records/5589597>`_.

EXIOBASE 3.8.2 was released in 2021. Its 2022 tables are estimated extensions of
the historical series. The data use CC-BY-SA-4.0. Retain the source attribution
when sharing derived results. The downloader API describes reuse and recovery
of interrupted downloads.
`EXIOBASE attribution <https://doi.org/10.1111/jiec.12715>`_,
`download API <https://www.marioproject.com/en/latest/api_document/mario.download_exiobase3.html>`_.

Database parsing
----------------

Read the economic flows from the monetary supply-use archive and attach the
satellite accounts from the matching IOT to their production activities.

.. code:: python

   db = mario.parse_exiobase(
       path=str(sut_path),
       table="SUT",
       unit="Monetary",
       add_extensions=str(iot_path),
   )

Transformation to single region
-------------------------------

Extract Italy and retain imported products in separate accounts. The commodity
classification identifies imported goods, while foreign origins and export
destinations are combined.

.. code:: python

   db.to_single_region(
       "IT",
       imports_by="commodity",
       import_representation="separate",
       trade_resolution="aggregate",
   )

``IMP_a`` records activity imports, ``IMP_c`` imports entering commodity supply,
and ``IMP_Y`` direct final-demand imports. The domestic accounts are represented
by ``U``, ``Yc`` and the factor matrices ``Va`` and ``VY``.
`Single-region API <https://www.marioproject.com/en/latest/api_document/mario.Database.to_single_region.html>`_.

.. _reference-system:

Aggregation
-----------

Combine the twelve electricity commodities into one ``Electricity`` product.
Apply the supplied aggregation workbook to the remaining products and activities.
It retains all twelve native electricity-generation technologies and combines
transmission and distribution in one activity. The commodity mappings also
aggregate the import accounts.

.. code:: python

   import pandas as pd

   commodities = db.get_index("Commodity")
   electricity = db.search("Commodity", "electricity ")
   assert len(electricity) == 12
   commodity_mapping = pd.DataFrame({"Aggregation": commodities}, index=commodities)
   commodity_mapping.loc[electricity, "Aggregation"] = "Electricity"
   db.aggregate(
       io={"Commodity": commodity_mapping},
       levels=["Commodity"],
       calc_all=False,
       zero_output_epsilon=None,
   )

Apply the ``Aggregation`` column after combining the electricity products.
The supplied workbook also provides five reporting groups per set in
``Aggregation II`` for the CVXLab visualizations.
The notebook checks the mapping coverage and the twelve retained technologies.

.. code:: python

   db.aggregate(
       io="aggregation.xlsx",
       levels=["Activity", "Commodity"],
       calc_all=False,
       zero_output_epsilon=None,
   )

GHG characterization
--------------------

Characterize greenhouse gases with the built-in EXIOBASE IPCC AR6 GWP100
profile. This indicator covers combustion CO2, CH4 and N2O as defined by that
profile. The retained indicator uses kg CO2-equivalent. Direct final-demand
emissions are represented in ``EY``.

.. code:: python

   ghg_label = "GHG AR6 GWP-100"
   db.calc_ghg(profile="exiobase_monetary", label=ghg_label)
   db.keep_extensions([ghg_label])

The aggregated reference has **18 products, 29 activities, 9 final-demand
categories, 12 factors of production and one GHG indicator**. The notebook checks
these dimensions and verifies ``IMP_a = imp_a × Xa`` column by column.
The following steps calibrate this reference before the calculation-path choice.

.. _calibrate-electricity-reference:

Update the reference electricity mix to 2022
-------------------------------------------

Before constructing scenarios, inspect the original generation shares and direct
intensities in the notebook. EXIOBASE 3.8.2 assigns very little Italian production
to photovoltaic electricity, with a high direct emission intensity; solar thermal
has negligible output and an extreme intensity. The notebook shows these original
values, then corrects the common reference in two steps.

First, apply the electricity preset with EMBER generation data for 2022:

.. code:: python

   db.update_supply_mix("electricity", year=2022)

The preset maps technologies to EXIOBASE activities, retains secondary electricity
production and rebuilds the economic flows. Physical generation shares are used
as monetary supply-share targets in this exercise; technology-specific electricity
prices are not modelled. The notebook compares the original and updated mixes.
The updated reference shares are reported in the problem statement.
`Electricity preset guide <https://www.marioproject.com/en/latest/user_guide/advanced/electricity_mix.html>`_.

Update direct electricity-emission intensities
----------------------------------------------

Second, take the direct monetary coefficients for all twelve Italian generation
technologies from the public EXIOBASE 3.11.2 industry-by-industry IOT for 2022.
The economic SUT remains EXIOBASE 3.8.2. Characterize the donor with the same
AR6 GWP100 profile before extracting ``e``. The IOT uses M.EUR and the SUT
uses EUR. Divide the donor coefficients by
1,000,000 before applying them, to express the receiving ``ea`` in
kg CO2-equivalent/EUR.

.. code:: python

   donor_dir = source_dir / "3.11.2"
   mario.download_exiobase3(
       path=donor_dir,
       years=[2022],
       table="IOT",
       system="ixi",
       version="3.11.2",
       extract=False,
   )
   donor = mario.parse_exiobase(
       path=str(donor_dir / "IOT_2022_ixi.zip"),
       table="IOT",
       unit="Monetary",
   )
   donor.calc_ghg(profile="exiobase_monetary", label=ghg_label)
   power_activities = db.search("Activity", "Production of electricity")
   donor_columns = [("IT", "Sector", activity) for activity in power_activities]
   donor_intensities = (
       donor.query("e").loc[ghg_label, donor_columns].droplevel([0, 1])
       / 1_000_000
   )
   del donor

The notebook builds one ``ea`` shock row per technology and uses ``type="Update"``
to replace the coefficients with ``shock_calc``. ``get_shock_excel`` provides the
blank native template; the filled shock table is passed in memory. For MARIO 1.3.5,
the notebook preserves the separate import blocks when materializing the correction,
then promotes the corrected scenario to the new baseline. The post-mix economic
coefficients and direct final-demand emissions retain their values.
These are direct coefficients: upstream emissions still follow the SUT input recipes.
`Shock API <https://www.marioproject.com/en/latest/api_document/mario.Database.shock_calc.html>`_.

The coefficients are obtained at execution time and are not shown in the page,
notebook outputs or distributed coefficient tables. Keep the source archives local.
The 3.11.2 source has its own non-commercial licence and attribution conditions.
`EXIOBASE 3.11.2 <https://zenodo.org/records/23039074>`_,
`source licence <https://zenodo.org/records/23039074/files/LICENSE.txt?download=1>`_.

.. _choose-the-calculation-path:

Continue in MARIO or CVXLab
---------------------------

* :ref:`Continue in MARIO <impact-scenario-analysis>` to calculate the scenarios
  and compare their accounting results with the methods in the notebook.
* :ref:`Continue in CVXLab <impact-continue-in-cvxlab>` to export this common reference and
  build the model described in the companion tutorial.

.. _impact-continue-in-cvxlab:

Continue in CVXLab
~~~~~~~~~~~~~~~~~~

Extract :download:`cvxlab_model.zip <cvxlab_model.zip>` beside the notebook,
then set ``continue_in_cvxlab = True``. The notebook calls ``db.to_cvxlab()``
to update all six reference input tables with its explicit name mappings,
including the activity outputs generated locally.
The classified ``sets.xlsx`` and the scenario shock tables are supplied.
The medium reporting aggregation retains the prepared reference labels.
The high reporting aggregation uses the five groups in ``Aggregation II``
for products and production activities.

The current CVXLab configuration combines ``U`` and ``Yc`` in ``use_0`` and
uses shared tables for imports and extensions. The combined extensions table
includes the structural zeros required for final-demand factors. The exporter
preserves the supplied scenario shocks. The published ``total_activity_0``
table retains its coordinates with blank values; the local export fills it.
The configuration and supplied reference flows are also stored in the tutorial
repository's ``cvxlab_model`` folder.
`CVXLab export guide <https://www.marioproject.com/en/latest/user_guide/inspection/to_cvxlab.html>`_.

.. important::

   The original CVXLab configuration uses ``minv(diag(X_0))`` and
   ``minv(diag(Q_0))`` to normalize reference flows. The Italian reference
   contains zero-output nuclear and tide/wave activities, making
   ``diag(X_0)`` singular.
   The exported inputs are populated and verified. The receiving model
   needs zero-safe coefficient normalization before its numerical solution.

The model-construction calls after the export are shown below. The exported
workbooks are the starting point for filling the receiving configuration.

.. code:: python

   import cvxlab

   model = cvxlab.Model(
       model_dir_name="cvxlab_model",
       model_settings_from="xlsx",
       use_existing_data=False,
       multiple_input_files=False,
       input_data_files_type="xlsx",
   )
   model.initialize_model_environment()
   model.refresh_database_and_initialize_problem(force_overwrite=True)
   model.run_model(
       solution_mode="sequential",
       sequential_solution_chain=["data_processing", "impact_analysis"],
   )
   model.load_results_to_database(force_overwrite=True)

MARIO exports monetary flows in EUR and GHG flows in kg CO2-equivalent. The
comparison uses M EUR and kt CO2-equivalent, obtained by dividing these flows
by 1,000,000. Align the receiving model's presentation units with its inputs.

`Continue with the CVXLab tutorial <https://cvxlab.readthedocs.io/en/dev/tutorials/input_output_analysis_mario/input_output_analysis_mario.html>`_.

.. _impact-scenario-analysis:

Scenario analysis in MARIO
--------------------------

High_RES
~~~~~~~~

The notebook's ``update_supply_mix`` call assigns the prescribed electricity
shares to the ``Electricity`` product and computes the associated quantity
model with fixed reference input, factor and emission coefficients.

.. code:: python

   db.update_supply_mix(
       {"IT": high_res_shares},
       scenario="High_RES",
       clone_from="baseline",
       level="Activity",
       commodities="Electricity",
       fill_missing_recipes=False,
   )

The notebook defines ``high_res_shares`` from the problem-statement table.
Italy has zero reference output for nuclear and tide/wave generation in this
source. The fixed-reference calculation retains their empty recipes, so their
activation contributes no intermediate inputs or direct emissions. Suitable
technology recipes are needed for a realistic interpretation of those activities.

High_RES_domestic
~~~~~~~~~~~~~~~~~

Clone ``High_RES`` and transfer electricity imports to the domestic electricity
row. Intermediate transfers update ``u`` and ``imp_a``. Final-demand transfers
update ``Yc`` and ``IMP_Y``. The notebook rebuilds the flows and checks that both
intermediate and direct final-demand electricity imports are zero.

.. _interpret-the-comparison:

Compare and interpret the results
---------------------------------

MARIO solves ``Xc = u @ Xa + Yc.sum(axis=1)`` and ``Xa = s @ Xc``, then reconstructs
the scenario accounts. Add intermediate and direct final-demand flows for each
indicator. The notebook reports absolute results and percentage changes from
Reference.

.. list-table:: Executed MARIO comparison
   :header-rows: 1

   * - Scenario
     - Factors of production (M EUR)
     - Imports (M EUR)
     - GHG (kt CO2-equivalent)
   * - Reference
     - 1,826,906.81
     - 502,514.90
     - 367,849.09
   * - High_RES
     - 1,826,922.28
     - 495,757.01
     - 285,066.97
   * - High_RES_domestic
     - 1,829,748.90
     - 492,271.09
     - 286,881.18

The downloadable ``scenario_summary.csv`` records the executed MARIO results
in M EUR and kt CO2-equivalent. The complete notebook shows their calculation
and the changes from the reference. The CVXLab equations were checked against
the same fixed-coefficient assumptions independently of its supplied workbooks.

Export the matrices and matching sets
-------------------------------------

The MARIO path writes nine labelled CSV matrices for all three scenarios,
``sets.xlsx`` and ``scenario_summary.csv`` under ``results``. The published
:download:`results.zip <results.zip>` contains those files. Their canonical
copies are stored in the tutorial repository beside the notebook.

.. _prepared-matrices:

.. list-table:: Exported MARIO matrices
   :header-rows: 1
   :widths: 24 38 38

   * - Matrix
     - Rows
     - Columns
   * - ``S``
     - Activities
     - Commodities
   * - ``U``
     - Commodities
     - Activities
   * - ``Yc``
     - Commodities
     - Final-demand categories
   * - ``Va``, ``Ea``
     - Factors of production or GHG indicator
     - Activities
   * - ``EY``
     - GHG indicator
     - Final-demand categories
   * - ``IMP_a``, ``IMP_Y``
     - Imported commodities
     - Activities or final-demand categories
   * - ``Xc``
     - Commodities
     - Output value

``IMP_c`` and ``VY`` are exactly zero in all three scenarios. The tutorial's
explicit public CSV export list omits them and ``Xa``. Corrected ``Ea`` and
``S`` remain included. ``Xa`` is generated locally for the CVXLab export.

CSV exports carry labelled coordinates, ``Value`` and ``Unit``. They retain
the raw EUR and kg CO2-equivalent units described above.

The complete export calls and coefficient checks are in the notebook.
`Export API <https://www.marioproject.com/en/latest/api_document/mario.Database.export.html>`_.
