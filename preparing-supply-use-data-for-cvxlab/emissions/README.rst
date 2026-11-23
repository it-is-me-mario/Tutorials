ISTAT 2022: emissions
=====================

This variant has 15 activities and products, 7 final-demand categories,
all 8 value-added/accounting rows and 25 satellite accounts.
The satellites are 24 AEA indicators and total employment.
Hours worked is excluded. AEA aggregates and components overlap; read
the indicators separately and do not sum them into a combined total.

Execute ``preparing_supply_use_data_for_cvxlab.ipynb`` from this folder with
MARIO 1.3.6 and CVXLab 1.0.1b1. The notebook downloads the official source,
parses, translates/aggregates, inspects and exports to ``cvxlab_model/``.
``aggregation.xlsx`` uses MARIO's native five-sheet mapping layout.
The source cache is not bundled. Cached satellite observations used for the
included results were retrieved on 20 November 2026.

The receiving settings and equations are unchanged. The input workbook has
``extensions_0`` with value added, activity satellites and household accounts;
there are no separate Ea/EY worksheets. The supplied delta templates are blank
and CVXLab applies their declared zero blank-fill when loading.

Source attribution and units are in ``cvxlab_model/README.rst``. That directory's
Apache-2.0 model licence is retained. This variant also includes
``cvxlab_model.zip`` for using the receiving model on its own.
