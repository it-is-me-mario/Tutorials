Prepare Italy's 2022 supply-use data for use in a CVXLab model.
Download the official ISTAT workbooks, attach compatible satellite accounts,
translate the labels into English, aggregate and inspect the database, then
export the matrices and sets to CVXLab.

This example uses the published national classifications. Electricity, gas,
steam and air conditioning remain one activity; no electricity-technology
disaggregation or power-sector scenarios are introduced.

Familiarity with supply-use tables is assumed. See
`MARIO table formats <https://www.marioproject.com/en/latest/get_started/table_formats.html>`_
for matrix structure and axes.

.. _problem-statement:

.. admonition:: Problem statement

   Prepare a national supply-use reference with domestic uses, separate product
   imports and compatible emissions, employment and energy accounts for a
   CVXLab model.

   Start from 63 ISTAT activities and products and obtain 15 of each, retaining
   7 final-demand categories, 8 income/accounting rows and 27 satellite accounts.
   Inspect the resulting reference and transfer it using the CVXLab model's
   table names, coordinates and filters.

.. _environment-and-inputs:
.. _run-the-tutorial:
.. _tutorial-materials:

.. rubric:: Tutorial materials

* :download:`Notebook <economy_wide_impact_assessment.ipynb>`: the complete
  download-to-export workflow, ending at ``to_cvxlab``.
* :download:`aggregation.xlsx <aggregation.xlsx>`: native MARIO mapping to
  15 activities and products, with English labels for all classifications.
* :download:`cvxlab_model.zip <cvxlab_model.zip>`: CVXLab model settings,
  classified sets and reference input tables.

Extract the archive beside the notebook to obtain ``cvxlab_model/``. Keep
``aggregation.xlsx`` in the same working folder. The readable companion is
available as :doc:`Notebook <notebook>`.

This workflow uses parser additions intended for MARIO 1.3.6, not included in
1.3.5. Install the development snapshot in a dedicated Python 3.12
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

.. _translate-the-classifications:
.. _reference-system:

Aggregation
-----------

``aggregation.xlsx`` maps the original ISTAT labels directly to the English
classifications used by the model. Its Activity and Commodity sheets aggregate
63 branches and products into 15 groups. Consumption category, Factor of
production and Satellite account provide one-to-one English labels.

The downloadable ``aggregation.xlsx`` is already filled in for this example.
To define a different mapping, generate a template from the parsed database
**before applying aggregation**:

.. code-block:: python

   db.get_aggregation_excel(
       path="my_aggregation.xlsx",
       levels=["Activity", "Commodity", "Consumption category",
               "Factor of production", "Satellite account"],
   )

Fill the ``Aggregation`` column in each sheet with the destination labels,
then pass ``io="my_aggregation.xlsx"`` to ``aggregate()``. Repeated destination
labels combine source items; one-to-one labels rename them. The template
does not choose the groups or translate labels automatically. A different
classification also needs compatible CVXLab set attributes. See the
`get_aggregation_excel API <https://www.marioproject.com/en/latest/api_document/mario.Database.get_aggregation_excel.html>`_.

The template-generation step is optional. To reproduce the example, use the
completed ``aggregation.xlsx`` from Tutorial materials.

Apply all five sheets in one call. Imports follow the commodity aggregation;
final-demand categories, factors and satellite indicators remain separate.
The monetary unit is renamed ``million EUR`` without numerical rescaling.

.. code-block:: python

   db.aggregate(
       io="aggregation.xlsx",
       levels=["Activity", "Commodity", "Consumption category",
               "Factor of production", "Satellite account"],
       calc_all=False,
       zero_output_epsilon=None,
   )

   for level in ["Activity", "Commodity", "Factor of production"]:
       db.units[level].loc[:, "unit"] = "million EUR"
   db.meta.model_configuration["import_unit"] = "million EUR"

Explore the reference
---------------------

Use ``get_index()`` to inspect the classifications and ``query()`` to retrieve
the matrices as pandas objects. ``db.get_index("Activity")`` returns the 15
activity labels; ``db.get_index("Consumption category")`` lists the seven
final-demand categories.

``db.query("S").shape`` is ``(15, 15)``: activities are rows and commodities
are columns. ``U`` has the reverse axes; ``Yc`` has commodities on rows and
final-demand categories on columns. The combined ``Z`` is ``(30, 30)`` and
``X`` is ``(30, 1)``. These combined views retain both productive
classifications; aggregation has not converted the SUT into a symmetric IOT.
The notebook includes a table of dimensions for the main blocks.

Domestic inputs, imports and value added
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare domestic intermediate purchases, imported intermediate purchases and
value-added/accounting items by activity, in million EUR:

.. code-block:: python

   import pandas as pd

   activity_inputs = pd.DataFrame({
       "Domestic intermediate inputs": db.query("U").sum(axis=0),
       "Imported intermediate inputs": db.query("IMP_a").sum(axis=0),
       "Value added/accounting items": db.query("Va").sum(axis=0),
   })
   activity_inputs.index = activity_inputs.index.get_level_values("Item")
   activity_inputs

``IMP_a`` is separate from ``Va``. Imports purchased directly by final-demand
categories are in ``IMP_Y`` and are not included in this activity table.
``Va`` retains all eight source income/accounting rows. Published monetary
rounding differences are retained.

Select an activity's supply
~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieve the products supplied by transport activities. ``query()`` returns
the complete matrix; ``xs()`` selects an item from its pandas MultiIndex:

.. code-block:: python

   db.query("S").xs("Transport activities", level="Item")

For an activity's purchases instead, select its column in ``U`` with
``db.query("U").xs("Transport activities", level="Item", axis=1)``.

Read satellite accounts with their units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The 27 satellite rows comprise 24 AEA indicators, employed persons, hours
worked and net domestic energy use. Inspect ``db.units["Satellite account"]``
before comparing values: emissions, employment and energy use different units.
For example, rank activities by direct production GHG emissions in t CO2-eq:

.. code-block:: python

   ghg = "Greenhouse gases (CO2 equivalent) [AEA: GHG]"
   db.query("Ea").loc[ghg].sort_values(ascending=False).head()

This selects a direct-flow row, not an emission intensity or a footprint
multiplier. ``GHG`` is already characterised: do not sum it with overlapping
gas components or equivalent versions. Direct household emissions are in
``EY``, which the notebook inspects separately. These national accounts do
not include emissions embodied in imports.

See the `inspection guide <https://www.marioproject.com/en/latest/user_guide/inspection/basic_inspections.html>`_
for more ways to retrieve classifications, matrices and units.

.. _impact-continue-in-cvxlab:

Export to CVXLab
----------------

``cvxlab_model/model_settings.xlsx`` defines the CVXLab sets, input tables,
variables and equations. The ``mapping`` argument links MARIO classifications
and matrices to these sets and tables. Activities and final demand share the
``accounts`` set; factors and satellites share ``extensions``.

The export populates six reference tables: ``make_0``, ``use_0``, ``imports_0``,
``extensions_0``, ``total_activity_0`` and ``total_demand_0``. ``use_0`` combines
``U`` and ``Yc``; ``imports_0`` combines ``IMP_a`` and ``IMP_Y``; ``extensions_0``
combines ``Va``, ``Ea`` and ``EY``.

This configuration has no exogenous ``VY`` input. That final-demand accounting
block remains in the MARIO database. The ``Reference`` scenario also contains
blank ``delta_make``, ``delta_use`` and ``delta_imports`` templates. CVXLab loads
them as zero according to ``blank_fill=0``; they appear as unmapped tables in
the export report because they are scenario inputs rather than MARIO matrices.

``to_cvxlab`` writes the classified sets to ``sets.xlsx`` and the input tables to
``input_data/input_data.xlsx`` inside ``cvxlab_model/``. Load these files into CVXLab using
the accompanying model configuration.

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
translated and productive classifications aggregated in this example.

Retain the
`ISTAT attribution and reuse notice <https://www.istat.it/note-legali/>`_,
`Eurostat source acknowledgement <https://ec.europa.eu/eurostat/help/copyright-notice>`_
and the receiving configuration's included licence when sharing the materials.
