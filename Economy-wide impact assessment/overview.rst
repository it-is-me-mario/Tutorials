This **twin tutorial** accompanies the **CVXLab** Python package's
`Economy-wide impact assessment tutorial <https://cvxlab.readthedocs.io/en/dev/tutorials/input_output_analysis_mario/input_output_analysis_mario.html>`_.
Both tutorials study electricity-supply changes through Leontief input-output
analysis. This Small Scale reference retains the twelve electricity-generation
technologies used by the CVXLab exercise.

* **The MARIO tutorial, this page**, obtains the source Supply and Use Tables,
  prepares the Italian reference, and calculates the electricity scenarios
  through MARIO's accounting and scenario methods.
* **The CVXLab tutorial** takes the prepared reference into its model data
  structures, defines and solves the mathematical problems, and analyses their
  results.

Complete the common data-preparation steps below, then choose whether to
continue the calculations in MARIO or export the reference to CVXLab.

Familiarity with input-output analysis is assumed. MARIO's Table formats guide
introduces the accounting structures used in the exercise.
`Table formats <https://www.marioproject.com/en/dev/get_started/table_formats.html>`_.

Start with a Python 3.12 Conda environment and the MARIO development revision
specified in the notebook. The CVXLab path also uses the CVXLab development
revision identified there. Installation guidance is available in
`MARIO getting started <https://www.marioproject.com/en/dev/get_started/index.html>`_
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
      \text{Coal} & 11.04\% & 0.0\% \\
      \text{Gas} & 62.94\% & 0.0\% \\
      \text{Nuclear} & 0.00\% & 15.0\% \\
      \text{Hydro} & 10.04\% & 9.0\% \\
      \text{Wind} & 1.38\% & 38.0\% \\
      \text{Petroleum} & 9.12\% & 0.0\% \\
      \text{Biomass and waste} & 1.92\% & 5.0\% \\
      \text{Solar photovoltaic} & 0.06\% & 31.0\% \\
      \text{Tide, wave, ocean} & 0.00\% & 0.5\% \\
      \text{Geothermal} & 1.60\% & 1.5\% \\
      \text{Others} & 1.91\% & 0.0\% \\
      \end{array}

   These are monetary production shares within the electricity-generation
   activities. Reference values come from the Italian EXIOBASE SUT used in the
   notebook. Others combines solar thermal and the remaining electricity
   activity. Secondary electricity production by other industries retains its
   reference market share. High RES shares specify the common teaching scenario.

   Calculate each scenario's percentage change in value added, imports and GHG
   emissions relative to Reference, then compare the two High RES outcomes.

.. _environment-and-inputs:
.. _run-the-tutorial:
.. _tutorial-materials:

.. rubric:: Tutorial materials

Use the following companions with this guide.

* :download:`economy_wide_impact_assessment.ipynb <economy_wide_impact_assessment.ipynb>`
  contains the complete MARIO workflow, installation commands and optional
  CVXLab export and model-construction calls.
* :download:`aggregation.xlsx <aggregation.xlsx>` supplies the Small Scale
  mapping with all twelve electricity-generation technologies retained.
* :download:`results.zip <results.zip>` contains the ten exported matrices,
  matching sets and summary for the three executed MARIO scenarios.
* :download:`scenario_summary.csv <scenario_summary.csv>` contains the executed
  MARIO comparison in M EUR and kt CO2-equivalent.
* :download:`cvxlab_model.zip <cvxlab_model.zip>` contains the CVXLab
  settings, classified sets, baseline inputs exported through ``to_cvxlab``
  and the three scenarios' shock tables.
* The `CVXLab tutorial materials <https://cvxlab.readthedocs.io/en/dev/_downloads/f16216b31c3f637ad45967d9f5ee116d/ioa_mario.zip>`_ provide its conceptual workbook
  and receiving model configuration for the optional CVXLab path.

Download the MARIO notebook, aggregation workbook and summary into one working folder. Follow the
steps below or run the notebook cells in sequence. An online version is
available as :doc:`Notebook <notebook>`.

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

The downloads total approximately 1 GB. The files can also be saved manually
in ``source_data`` from the official EXIOBASE record.
`EXIOBASE 3.8.2 <https://zenodo.org/records/5589597>`_.

EXIOBASE 3.8.2 was released in 2021. Its 2022 tables are estimated extensions of
the historical series. The data use CC-BY-SA-4.0. Retain the source attribution
when sharing derived results. The downloader API describes reuse and recovery
of interrupted downloads.
`EXIOBASE attribution <https://doi.org/10.1111/jiec.12715>`_,
`download API <https://www.marioproject.com/en/dev/api_document/mario.download_exiobase3.html>`_.

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
`Single-region API <https://www.marioproject.com/en/dev/api_document/mario.Database.to_single_region.html>`_.

GHG characterization
--------------------

Characterize greenhouse gases with the built-in EXIOBASE IPCC AR6 GWP100
profile. The retained indicator uses kg CO2-equivalent. Direct final-demand
emissions are represented in ``EY``.

.. code:: python

   ghg_label = "GHG AR6 GWP-100"
   db.calc_ghg(profile="exiobase_monetary", label=ghg_label)
   db.keep_extensions([ghg_label])

.. _reference-system:

Aggregation
-----------

Combine the twelve electricity commodities into one ``Electricity`` product.
Apply the supplied Small Scale workbook to the remaining products and activities.
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

Apply the Small Scale workbook after combining the electricity products.
The notebook checks the mapping coverage and the twelve retained technologies.

.. code:: python

   db.aggregate(
       io="aggregation.xlsx",
       levels=["Activity", "Commodity"],
       calc_all=False,
       zero_output_epsilon=None,
   )

The prepared reference has **45 products, 56 activities, 9 final-demand
categories, 12 factors of production and one GHG indicator**. The notebook checks
these dimensions and verifies ``IMP_a = imp_a × Xa`` column by column. It also
shows the generation-activity shares used in the problem statement and the
separate contribution of secondary electricity production.

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
to update the six reference input tables with its explicit name mappings.
The classified ``sets.xlsx`` and the scenario shock tables are supplied.
Reporting aggregations retain the Small Scale member labels.

The current CVXLab configuration combines ``U`` and ``Yc`` in ``use_0`` and
uses shared tables for imports and extensions. The combined extensions table
includes the structural zeros required for final-demand factors. The exporter
preserves the supplied scenario shocks. The complete configuration and inputs
are also stored in the tutorial repository's ``cvxlab_model`` folder.
`CVXLab export guide <https://www.marioproject.com/en/dev/user_guide/inspection/to_cvxlab.html>`_.

.. important::

   The original CVXLab configuration uses ``minv(diag(X_0))`` and
   ``minv(diag(Q_0))`` to normalize reference flows. The Italian reference
   contains zero-output members, making these matrices singular.
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

The CVXLab page explains its model definition, file setup and solution steps.
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
     - 1,825,700.67
     - 503,721.04
     - 327,854.04
   * - High_RES
     - 1,826,760.10
     - 495,917.30
     - 292,551.29
   * - High_RES_domestic
     - 1,829,567.64
     - 492,450.95
     - 295,472.73

The downloadable ``scenario_summary.csv`` records the executed MARIO results
in M EUR and kt CO2-equivalent. The complete notebook shows their calculation
and the changes from the reference. The CVXLab equations were checked against
the same fixed-coefficient assumptions independently of its supplied workbooks.

Export the matrices and matching sets
-------------------------------------

The MARIO path writes ten labelled CSV matrices for all three scenarios,
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
   * - ``Xa``, ``Xc``
     - Activities or commodities
     - Output value

``IMP_c`` and ``VY`` are exactly zero in all three scenarios. The tutorial's
explicit CSV export list omits them.

CSV exports carry labelled coordinates, ``Value`` and ``Unit``. MARIO writes
monetary flows in EUR and GHG flows in kg CO2-equivalent. CVXLab's tutorial
presents M EUR and kt CO2-equivalent, obtained by dividing these flow values
by 1,000,000. Use a consistent scale in the receiving model.

The complete export calls and coefficient checks are in the notebook.
`Export API <https://www.marioproject.com/en/dev/api_document/mario.Database.export.html>`_.
