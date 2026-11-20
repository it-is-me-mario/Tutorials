Prepare Italy's 2022 national supply-use table for the MARIO–CVXLab exercise.
Download the official ISTAT workbooks, attach compatible satellite accounts,
translate the labels into English, aggregate and inspect the database, then
export the reference to CVXLab. This tutorial ends at that handoff.

The exercise uses the published national classifications. Electricity, gas,
steam and air conditioning remain one activity; no electricity-technology
disaggregation or power-sector scenarios are introduced.

Familiarity with supply-use tables is assumed. See
`MARIO table formats <https://www.marioproject.com/en/latest/get_started/table_formats.html>`_
for matrix structure and axes.

.. _problem-statement:

.. admonition:: Problem statement

   How can we prepare a national supply-use reference with domestic uses,
   separate product imports and compatible emissions, employment and energy
   accounts for a CVXLab model?

   Start from 63 ISTAT activities and products and obtain 15 of each, retaining
   7 final-demand categories, 8 income/accounting rows and 27 satellite accounts.
   Inspect the resulting reference and transfer it using the supplied model's
   table names, coordinates and filters.

.. _environment-and-inputs:
.. _run-the-tutorial:
.. _tutorial-materials:

.. rubric:: Tutorial materials

* :download:`Notebook <economy_wide_impact_assessment.ipynb>`: the complete
  download-to-export workflow, ending at ``to_cvxlab``.
* :download:`translations.xlsx <translations.xlsx>`: one-to-one English labels.
* :download:`aggregation.xlsx <aggregation.xlsx>`: native MARIO mapping to
  15 activities and products.
* :download:`cvxlab_model.zip <cvxlab_model.zip>`: Matteo's supplied settings,
  English classified sets and prepared CVXLab reference inputs.

Extract the archive beside the notebook to obtain ``cvxlab_model/``. Keep both
mapping workbooks in the same working folder. The readable companion is
available as :doc:`Notebook <notebook>`.

This workflow uses parser additions intended for MARIO 1.3.6, not included in
1.3.5. Use the verified development snapshot in a dedicated Python 3.12
environment and restart the notebook kernel after installation:

.. code-block:: bash

   conda create -n mario_cvxlab_tutorial python=3.12 pip
   conda activate mario_cvxlab_tutorial
   python -m pip install "mariopy @ git+https://github.com/it-is-me-mario/MARIO.git@e786e43fd01186bf1707cf098e2ceea1afb29e49" "cvxlab==1.0.1b1" jupyterlab
   python -m jupyter lab

.. _prepare-the-reference-system:

Database download
-----------------

Download the official `ISTAT 2020–2022 edition <https://www.istat.it/tavole-di-dati/il-sistema-di-tavole-input-output-anni-2020-2022/>`_.
The parser selects 2022 at current basic prices. The native classification
contains 63 NACE Rev. 2 branches and 63 CPA 2.1 products, excluding
extraterritorial organisations. Existing cached workbooks are reused.

.. code-block:: python

   import mario

   mario.download_istat_io(path="source_data", edition="2020-2022")

The source archive and selected satellite snapshots are cached under
``source_data/``. Preserve that cache to retain the exact source vintages.

.. _transformation-to-single-region:

Database parsing
----------------

Read SUPPLY, USE and IMPORT and select the three optional satellite
groups. ``download=True`` reuses the monetary release and fetches missing
Eurostat snapshots for Italy in the same reference year.

ISTAT is already single-region: do not call ``to_single_region()``.
``IMP_a`` and ``IMP_Y`` retain imports by product and purchasing activity or final
demand. ``U`` and ``Yc`` contain domestic uses; no origin-country detail is available.

The selected accounts are `AEA emissions <https://ec.europa.eu/eurostat/databrowser/view/env_ac_ainah_r2/default/table?lang=en>`_,
`employment <https://ec.europa.eu/eurostat/databrowser/view/nama_10_a64_e/default/table?lang=en>`_
and `PEFA net domestic energy use <https://ec.europa.eu/eurostat/databrowser/view/env_ac_pefa04/default/table?lang=en>`_.
Hours worked come from the ISTAT USE workbook. Production accounts populate
``Ea``; direct household emissions and energy populate ``EY``. ``Ec`` is zero.
Native NACE codes align the satellite observations before labels are translated.
Missing required observations cause an error rather than being filled with zero.

.. code-block:: python

   db = mario.parse_istat(
       path="source_data",
       year=2022,
       table="SUT",
       level="63",
       price="current",
       valuation="basic",
       import_representation="separate",
       extensions=["emissions", "employment", "energy"],
       download=True,
       edition="2020-2022",
   )

See the source snapshot's
`ISTAT parser guide <https://github.com/it-is-me-mario/MARIO/blob/e786e43fd01186bf1707cf098e2ceea1afb29e49/doc/source/notebooks/parsers/istat/walkthrough_istat.rst>`_
for optional satellite selection, units and cache behaviour.

Translate the classifications
-----------------------------

Apply ``translations.xlsx`` as a one-to-one mapping across all five
classifications. It changes labels, not values. Activities, commodities, final
demand, factors and satellites are then named in English. AEA labels spell out
the indicator and retain its source code. The monetary unit is renamed
``million EUR``; no numerical rescaling is applied.

The notebook applies this mapping with ``aggregate()`` before the sector
aggregation. Both mappings are standard MARIO workbooks; they add no
presentation formatting.

.. _reference-system:

Aggregation
-----------

Apply the supplied native MARIO workbook to activities and commodities.
Its two sheets contain the source label and ``Aggregation`` columns without
custom formatting. Translation has already put their source labels in English.
Imports follow the commodity aggregation. No satellite indicators are merged.

.. code-block:: python

   db.aggregate(
       io="aggregation.xlsx",
       levels=["Activity", "Commodity"],
       calc_all=False,
       zero_output_epsilon=None,
   )

Explore the reference
---------------------

Inspect the classifications, units and representative blocks before
export. The combined SUT is 30 × 30, with a 30 × 1 production vector; it remains
a supply-use system rather than a symmetric IOT.

The 27 satellite rows comprise 24 AEA indicators, employed persons, hours worked
and net domestic energy use in TJ. ``Greenhouse gases (CO2 equivalent) [AEA: GHG]``
is already characterised in t CO2-eq: do not sum it with overlapping gas
components or equivalent versions. These direct national accounts do not add
the emissions embodied in imported goods. Published monetary rounding
differences are retained.

Use ``get_index("all")``, ``units["Satellite account"]`` and ``query()`` in the
notebook to inspect ``S``, ``IMP_a`` and ``Ea``. Review English final-demand
labels and ``EY`` when checking the household accounts.

.. _impact-continue-in-cvxlab:

Export to CVXLab
----------------

Use the supplied ``cvxlab_model/model_settings.xlsx`` as the target contract.
The export keeps its equations and variable definitions. Activities and final
demand share the ``accounts`` set; factors and satellites share ``extensions``.

The method populates six reference tables: ``make_0``, ``use_0``, ``imports_0``,
``extensions_0``, ``total_activity_0`` and ``total_demand_0``. ``use_0`` combines ``U``
and ``Yc``; ``imports_0`` combines ``IMP_a`` and ``IMP_Y``; ``extensions_0`` combines
``Va``, ``Ea`` and ``EY``.

The supplied configuration does not declare an exogenous ``VY`` input. That
nonzero final-demand accounting block remains in the MARIO object and is not
inserted into an undeclared CVXLab table. The ``Reference`` scenario has blank
``delta_make``, ``delta_use`` and ``delta_imports`` templates; CVXLab applies the
configuration's ``blank_fill=0`` when loading them. They remain listed as unmapped
tables in the export report because they are CVXLab scenario inputs.

The complete ``cvxlab_model/`` directory is the handoff. The generated input cells
and their loading into CVXLab SQLite have been verified. Defining and solving
analysis scenarios belongs to the receiving CVXLab exercise and is outside
this notebook.

.. code-block:: python

   report = db.to_cvxlab(
       model_settings="cvxlab_model/model_settings.xlsx",
       path="cvxlab_model",
       mapping={
           "sets": {
               "Commodity_from": "products", "Commodity_to": "products",
               "Activity_from": "accounts", "Activity_to": "accounts",
               "Consumption category_to": "accounts",
               "Factor of production_from": "extensions",
               "Satellite account_from": "extensions",
           },
           "matrices": {
               "S": "make_0", "U": "use_0", "Yc": "use_0",
               "IMP_a": "imports_0", "IMP_Y": "imports_0",
               "Va": "extensions_0", "Ea": "extensions_0", "EY": "extensions_0",
               "Xa": "total_activity_0", "Xc": "total_demand_0",
           },
       },
   )
   report["written_cells"]

Source attribution
------------------

The monetary workbooks are from ISTAT's 2020–2022 edition, with observation
year 2022. Satellite data are from the linked Eurostat datasets, accessed
20 November 2026; hours worked are from the ISTAT USE workbook. Labels were
translated and productive classifications aggregated for this exercise.

Retain the
`ISTAT attribution and reuse notice <https://www.istat.it/note-legali/>`_,
`Eurostat source acknowledgement <https://ec.europa.eu/eurostat/help/copyright-notice>`_
and the receiving configuration's included licence when sharing the materials.
