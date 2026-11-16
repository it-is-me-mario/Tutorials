Use BONSAI's native **b2 HIOT** to calculate GHG footprint multipliers and
compare them with the corresponding BONSAI GWP100 export. The notebook uses
the ``20260615`` release folder; its contents can change, so record the files
and their dates.

Inputs
------

Obtain the HIOT files from the BONSAI team. Keep these four files from the
same release in one directory:

* ``extended_size_hiot.b2.pkl``: native technosphere;
* ``final_demand.b2.csv``: final demand;
* ``total_elementary_flow_w_iLUC.csv``: elementary flows, including iLUC;
* ``ghg_for_all.b2.GWP100.csv``: BONSAI reference footprints.

The notebook includes access instructions and an optional UMFPACK installation
step. Restart the kernel if that step installs packages. The footprint workflow
uses the HIOT only; a Balanced HSUT is needed only for the optional HSUT import
in the preceding section.

Calculation
-----------

1. Import the HIOT with ``mario.parse_bonsai(..., table="IOT")`` and inspect
   regional classifications, units and import diagnostics as above.
2. Select UMFPACK and call ``calc_ghg(label="GHG")``. MARIO's BONSAI profile
   uses AR6 GWP100 by default, including the characterized accelerated-CO2 flow.
3. Retain the GHG account and request ``db.f``. These are footprints **per native
   product unit**, not total final-demand footprints. Units differ by product.
4. Match MARIO and BONSAI results by region and product, then save
   ``footprint_ghg_comparison.csv``.

The comparison reports ``(MARIO - BONSAI) / BONSAI``: ``0.01`` means MARIO is
1% higher. Zero denominators and unmatched region/product pairs remain missing.
Check the release, elementary flows and characterization factors before
interpreting differences.
