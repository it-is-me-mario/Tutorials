Prepare Italy's 2022 supply-use data for use in a CVXLab model.
Download the official ISTAT workbooks, attach greenhouse-gas emissions, employment and energy accounts,
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

   Prepare a national supply-use database with domestic uses, separate product
   imports and compatible greenhouse-gas emissions, employment and energy accounts for a
   CVXLab model.

   Start from 63 ISTAT activities and products and obtain 15 of each, retaining
   7 final-demand categories, 8 income/accounting rows and 3 satellite accounts.
   Inspect the database and export its baseline matrices using the CVXLab model's
   table names, coordinates and filters.

.. _environment-and-inputs:
.. _run-the-tutorial:
.. _tutorial-materials:

.. rubric:: Tutorial materials

* :download:`Notebook <preparing_supply_use_data_for_cvxlab.ipynb>`: the complete
  download-to-export workflow, ending at ``to_cvxlab``.
* :download:`aggregation.xlsx <aggregation.xlsx>`: native MARIO mapping to
  15 activities and products, with English labels for all classifications.
* :download:`cvxlab_model.zip <cvxlab_model.zip>`: CVXLab model settings,
  classified sets and input tables.

Extract the archive beside the notebook to obtain ``per cvxlab/``. Keep
``aggregation.xlsx`` in the same working folder. The readable companion is
available as :doc:`Notebook <notebook>`.

.. _additional-satellite-variants:

.. rubric:: Additional satellite variants

Two separate folders provide broader AEA emission selections. Each download contains
its own notebook, aggregation mapping, classified CVXLab sets and generated
input data. Run the notebook from the extracted folder. Both variants keep
the same 15 activities/products, 7 final-demand categories and all 8
value-added/accounting rows.

.. list-table:: Alternative satellite selections
   :header-rows: 1
   :widths: 25 50 25

   * - Variant
     - Satellite accounts
     - Download
   * - Emissions
     - 24 AEA emission indicators and total employment
     - :download:`ZIP <emissions.zip>`
   * - Emissions and energy
     - 24 AEA emission indicators, total employment and net domestic energy use
     - :download:`ZIP <emissions-and-energy.zip>`

AEA includes gas masses and characterised totals with different units.
Totals overlap their components: do not sum the GHG total with its gases
or with other environmental indicators. Each variant retains the native
units in MARIO and lists them in its CVXLab package's README.

.. rubric:: Installation

Use MARIO 1.3.6 in a dedicated Python 3.12 environment. This release includes
the ISTAT import and satellite options used below. Restart the notebook
kernel after installation:

.. code-block:: bash

   conda create -n mario_cvxlab_tutorial python=3.12 pip
   conda activate mario_cvxlab_tutorial
   python -m pip install "mariopy==1.3.6" "cvxlab==1.0.1b1" jupyterlab
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

Read SUPPLY, USE and IMPORT and request the emissions, employment and energy
groups. ``download=True`` reuses the monetary release and fetches missing
Eurostat snapshots for Italy in the same reference year.

ISTAT is already single-region: do not call ``to_single_region()``.
``IMP_a`` and ``IMP_Y`` retain imports by product and purchasing activity or final
demand. ``U`` and ``Yc`` contain domestic uses; no origin-country detail is available.

The sources are `air emissions accounts <https://doi.org/10.2908/env_ac_ainah_r2>`_,
`employment <https://doi.org/10.2908/nama_10_a64_e>`_ and
`PEFA net domestic energy use <https://doi.org/10.2908/env_ac_pefa04>`_.
The parser groups contain additional indicators. ``keep_extensions()`` selects
exactly the GHG total, total employment and net domestic energy use, while
preserving every factor of production. Hours worked and the other emission
indicators are excluded. The aggregation workbook contains these same three
satellite rows and translates their labels into English.

Activity accounts populate ``Ea``; direct household emissions and energy use
populate ``EY``. Their units are tonnes CO2 equivalent, persons and TJ.
The GHG total is characterised: do not add its component gases to it.
Native NACE codes align observations before labels are translated.
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

   db.keep_extensions([
       "AEA | GHG",
       "Employment | Total",
       "Energy | Net domestic energy use",
   ])
   db.get_index("Satellite account")

The variable ``db`` is a ``mario.Database`` object: it contains the SUT,
classifications, units, metadata and scenarios. The parsed matrix values
belong to its ``baseline`` scenario, which is used throughout this example.
See `Objects in MARIO <https://www.marioproject.com/en/latest/get_started/table_formats.html#objects-in-mario>`_
for the distinction between a database, a table, a scenario and a matrix.

See the
`ISTAT parser guide <https://www.marioproject.com/en/latest/notebooks/parsers/istat/walkthrough_istat.html>`_
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

.. _explore-the-reference:

Explore the database
--------------------

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieve the products supplied by transport activities. ``query()`` returns
the complete matrix; ``xs()`` selects an item from its pandas MultiIndex:

.. code-block:: python

   db.query("S").xs("Transport activities", level="Item")

For an activity's purchases instead, select its column in ``U`` with
``db.query("U").xs("Transport activities", level="Item", axis=1)``.

Read satellite accounts with their units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The database retains greenhouse-gas emissions in tonnes CO2 equivalent,
total employment in persons and net domestic energy use in TJ. Inspect ``db.units["Satellite account"]``
before comparing their values. For example, rank activities by employment:

.. code-block:: python

   employment = "Total employment (domestic concept)"
   db.query("Ea").loc[employment].sort_values(ascending=False).head()

The notebook also inspects direct household emissions and energy use in ``EY``,
separately from the activity accounts in ``Ea``. The three indicators have
different units and should be read separately.

See the `inspection guide <https://www.marioproject.com/en/latest/user_guide/inspection/basic_inspections.html>`_
for more ways to retrieve classifications, matrices and units.

.. _impact-continue-in-cvxlab:

Export to CVXLab
----------------

``per cvxlab/model_settings.xlsx`` defines the CVXLab sets, database tables,
variables and equations. ``to_cvxlab()`` exports the matrices of the MARIO
database's ``baseline`` scenario. The ``mapping`` argument connects their axes
to CVXLab sets and assigns each matrix to a CVXLab input table. The variables
in those tables are defined by the model settings:

.. list-table:: MARIO matrices and CVXLab inputs
   :header-rows: 1
   :widths: 24 30 46

   * - MARIO matrix
     - CVXLab input variable
     - CVXLab database table
   * - ``S``
     - ``S_0``
     - ``make_0``
   * - ``U``
     - ``U_0``
     - ``use_0``
   * - ``Yc``
     - ``Y_0``
     - ``use_0``
   * - ``IMP_a``
     - ``IMP_a_0``
     - ``imports_0``
   * - ``IMP_Y``
     - ``IMP_y_0``
     - ``imports_0``
   * - ``Va``
     - ``V_a_0``
     - ``extensions_0``
   * - ``Ea``
     - ``E_a_0``
     - ``extensions_0``
   * - ``EY``
     - ``E_y_0``
     - ``extensions_0``
   * - ``Xa``
     - ``X_a_0``
     - ``total_activity_0``
   * - ``Xc``
     - ``X_c_0``
     - ``total_demand_0``

The ``_0`` suffix identifies input variables in this model configuration.
These six input tables contain the baseline values exported from MARIO.
Several variables share a table: ``U_0`` and ``Y_0`` select intermediate and
final-demand columns from ``use_0``; the import variables use the same split
in ``imports_0``. Within ``extensions_0``, ``V_a_0`` selects value-added rows,
while ``E_a_0`` and ``E_y_0`` select satellite rows for production and final
demand. These selections use the category attributes in ``sets.xlsx``.

Activities and final demand share the ``accounts`` set; factors and satellites
share ``extensions``. This configuration has no exogenous input for ``VY``;
that final-demand accounting matrix remains in the MARIO database.

CVXLab scenario inputs
~~~~~~~~~~~~~~~~~~~~~~~~~~

``model_settings.xlsx`` declares ``delta_use``, ``delta_imports`` and
``delta_extensions`` as additional input tables. ``to_cvxlab()`` creates their
templates but leaves their values blank because they have no MARIO matrix
mapping. They appear in ``report["unmapped_tables"]`` and can also appear in
``report["missing_values"]``. CVXLab supplies zeros using the configuration's
``blank_fill=0`` when loading them; MARIO does not calculate scenario shocks.

The supplied sets preserve four CVXLab scenario names: ``reference``,
``domestic_energy``, ``petroleum_free_transport`` and ``mixed``. The six
``_0`` tables contain the MARIO ``baseline`` values without a scenario
dimension. ``delta_use`` and ``delta_imports`` have a scenario dimension;
``delta_extensions`` does not in this configuration.

Write CVXLab inputs
~~~~~~~~~~~~~~~~~~~~~~~~~

``to_cvxlab()`` writes the classified sets to ``sets.xlsx`` and the input tables
to ``input_data/input_data.xlsx`` inside ``per cvxlab/``. Load these files
into CVXLab using the accompanying model configuration.
The supplied ``sets.xlsx`` contains the final member order, categories,
reporting groups and scenario names; the export preserves them. Blank
``type`` attributes intentionally leave members outside the ``power`` filter.
They may be flagged in ``report["missing_attributes"]`` and do not represent
missing matrix values.


.. code-block:: python

   report = db.to_cvxlab(
       model_settings="per cvxlab/model_settings.xlsx",
       path="per cvxlab",
       sync_sets=["extensions"],
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

``sync_sets=["extensions"]`` keeps the receiving extension set aligned with
the mapped value-added and selected satellite accounts. When regenerating
files from an earlier selection, MARIO removes obsolete indicators and their
dependent input rows while preserving the retained set attributes and all
mapped value-added accounts. Inspect ``report["removed_set_members"]`` and
``report["removed_input_rows"]`` to review any removals.

Source attribution
------------------

The monetary workbooks are from ISTAT's 2020–2022 edition, with observation
year 2022. Emissions, employment and energy data are from the linked Eurostat datasets,
accessed 24 November 2026. Labels were
translated and productive classifications aggregated in this example.

Retain the
`ISTAT attribution and reuse notice <https://www.istat.it/note-legali/>`_,
`Eurostat source acknowledgement <https://ec.europa.eu/eurostat/help/copyright-notice>`_
and the receiving configuration's included licence when sharing the materials.
