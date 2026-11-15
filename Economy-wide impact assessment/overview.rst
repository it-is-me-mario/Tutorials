Prepare Italy's 2022 reference supply-use system with separate import accounts,
then continue with the electricity-generation scenarios in CVXLab. This is the
MARIO half of `Economy-wide impact assessment
<https://cvxlab.readthedocs.io/en/dev/tutorials/input_output_analysis_mario/input_output_analysis_mario.html>`_.

Reference system
----------------

The exercise retains the full classification described by the CVXLab tutorial.
The resulting Italian system has **189 products, 163 activities, 9 final-demand
categories, 12 factors of production and one GHG indicator**. Electricity
commodities are combined into one product, while generation technologies retain
their individual activities.

The notebook produces twelve labelled CSV matrices and ``sets.xlsx``. Imports
have their own matrices, with one row per imported commodity. The value-added
matrix retains the domestic factors of production.

Environment and inputs
----------------------

Use Python 3.12 and the `verified MARIO development revision
<https://github.com/it-is-me-mario/MARIO/tree/f137208feb031d8eb452a27f33336424767d17b5>`_.
The separate-import configuration used here is under development and requires
this revision. Install it in an environment for the tutorial::

   python -m pip install "mariopy @ git+https://github.com/it-is-me-mario/MARIO.git@f137208feb031d8eb452a27f33336424767d17b5" jupyterlab

Download the following archives from the official `EXIOBASE 3.8.2 record
<https://zenodo.org/records/5589597>`_ and place them in ``source_data`` beside
the notebook. The combined downloads occupy approximately 1 GB.

* ``MRSUT_2022.zip`` supplies the monetary supply-use tables.
* ``IOT_2022_ixi.zip`` supplies the matching satellite accounts.

EXIOBASE 3.8.2 was published in 2021. Its 2022 tables are estimated extensions
of the historical series. The source data use CC-BY-SA-4.0. Retain the
`EXIOBASE attribution <https://doi.org/10.1111/jiec.12715>`_ when reusing results.

Prepare the reference system
----------------------------

1. Parse the SUT and attach the satellite accounts from the matching IOT.
2. Extract Italy, keeping commodity imports in separate matrices and combining
   foreign origins and export destinations.
3. Characterise GHG emissions using IPCC AR6 GWP100 and combine electricity
   commodities into one product.
4. Check the dimensions and import coefficients, then export the matrices
   and the matching sets.

The key configuration is::

   db.to_single_region(
       "IT",
       imports_by="commodity",
       import_representation="separate",
       trade_resolution="aggregate",
   )

Matrices for CVXLab
-------------------

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
   * - ``VY``, ``EY``
     - Factors of production or GHG indicator
     - Final-demand categories
   * - ``IMP_a``, ``IMP_c``, ``IMP_Y``
     - Imported commodities
     - Activities, commodities or final-demand categories
   * - ``Xa``, ``Xc``
     - Activities or commodities
     - Output value

CSV exports carry labelled coordinates, ``Value`` and ``Unit``. MARIO writes
monetary flows in EUR and GHG flows in kg CO2-equivalent. CVXLab's tutorial
presents M EUR and kt CO2-equivalent, obtained by dividing these flow values
by 1,000,000. Use a consistent scale in the receiving model.

The receiving CVXLab settings must match the full classification, separate
matrices and units. Continue with the `CVXLab tutorial
<https://cvxlab.readthedocs.io/en/dev/tutorials/input_output_analysis_mario/input_output_analysis_mario.html>`_
to formulate and solve the generation scenarios.

See MARIO's `single-region API
<https://www.marioproject.com/en/latest/api_document/mario.Database.to_single_region.html>`_
and `export API
<https://www.marioproject.com/en/latest/api_document/mario.Database.export.html>`_
for the operations demonstrated by the notebook.
