Tutorial site maintenance
========================

Sources and ownership
---------------------

``catalog.json`` owns the tutorial routes, summaries, source repositories and
material lists. Edit each notebook in its listed source repository. The build
creates temporary render and download copies under ``_build``; these copies are
excluded from Git. The source repository's history and original URLs remain the
permanent record.

The shared MARIO theme is imported at the full commit recorded in the catalogue.
Review its templates, CSS, scripts and logo assets together when updating that
commit. ``conf.py`` supplies this site's navigation and search index. The footer
override supplies links to the main MARIO site. ``_static/tutorials.css`` owns
notebook layout adaptations.

``build.py`` resolves each external ref once per build. All files belonging to
that source use that same commit. ``source-manifest.json`` records the publisher,
theme, source commits and source/download hashes. Notebook cleaning preserves
every source cell and removes stored outputs. Calculations are executed and
verified separately when maintaining the source tutorial.

Local verification
------------------

Install Pandoc and the dependencies in ``requirements.txt``, then run from the
repository root::

   python -m pip install -r site/requirements.txt
   python -m unittest discover -s site/tests -v
   python site/build.py
   python site/check.py _site
   python -m http.server 8767 --directory _site

Keep the clean CI build passing with these requirements alone. IPython supplies
the notebook's ``ipython3`` syntax lexer, including cells containing magics.

Review the index, each notebook, all companion downloads, the source-revision
links, desktop/mobile navigation and dark/light themes. Compare code cells in
published companions with their canonical source. Report notebook calculations
separately from rendering and publication checks.

Publication and external refreshes
---------------------------------

The workflow in ``.github/workflows/pages.yml`` publishes pushes to main after
tests, the strict Sphinx build and local-link/download checks. Pull requests build
and verify the site. GitHub Pages must be enabled using the Actions build mode.
The workflow reads the site's current address from GitHub Pages settings, so
switching between the project URL and its custom domain uses the same build.

MRIO disaggregation's notification workflow invokes this publication through
``workflow_dispatch``. Configure its ``TUTORIALS_PUBLISH_TOKEN`` repository secret
with a fine-grained token whose selected repository is Tutorials and whose only
additional repository permission is Actions read/write. Its default Metadata
read permission supplies repository identity. Keep that credential in the source
repository's Actions secret store.

The hourly revision check also detects changes in registered external refs and
publishes only when the deployed manifest differs. GitHub can delay scheduled
runs and disables schedules on inactive public repositories. Check the Actions
history when auditing refreshes; use the manual publication action for an
immediate rebuild. A frozen workshop edition can select a tag or full commit in
the catalogue.

Before merging, inspect the branch rules, PR checks and reviews. After publication,
check the deployed manifest against the intended commits, open representative
public pages and download the notebooks and supporting files. A local preview
does not verify the published site.

Configure a custom domain in GitHub Pages after its DNS CNAME resolves to the
organization's GitHub Pages hostname. Verify the HTTPS certificate and enable
HTTPS enforcement once GitHub has provisioned it. Main MARIO navigation changes
belong in its own documentation migration.
