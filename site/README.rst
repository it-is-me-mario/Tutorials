Tutorial site maintenance
========================

Sources and ownership
---------------------

``versions.json`` selects the content refs for Latest and Dev. Latest uses the
existing root routes, and Dev is published under ``/dev/``. The publisher reads
each catalogue, notebook, guide and material at the selected commit. Source
notebooks remain in their canonical repositories. The shared frontend is pinned
by the publisher's catalogue and used for both channels.

``versions-manifest.json`` records the publisher and both sets of resolved source
commits. Each channel also retains its own ``source-manifest.json`` and downloads.
``docs-versions.json`` records available HTML pages and anchors for the common
Latest/Dev selector. Its native links open each channel home when scripts are
unavailable. A missing counterpart page falls back to that home.

``catalog.json`` owns the tutorial routes, summaries, source repositories and
material lists. Edit each notebook in its listed source repository. The build
creates temporary render and download copies under ``_build``; these copies are
excluded from Git. The source repository's history and original URLs remain the
permanent record.

An optional ``guide`` names an RST explanation from the notebook's source and
revision. The publisher includes a generated ``.rst.inc`` copy in the landing
page and records its hash. Keep the full calculation in the notebook companion.

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

Check that links among the main documentation, Tutorials and Database Explorer
use the current tab when updating the shared theme.

Review both channel homes, a shared tutorial page and a Dev-only exercise.
Check the selector, same-page/anchor switching, fallback, download hashes and
navigation to the corresponding MARIO and Explorer channel. Run the source
calculations separately when changing a notebook. The website build renders
and cleans notebooks without executing their calculations.

Publication and external refreshes
---------------------------------

The workflow in ``.github/workflows/pages.yml`` publishes pushes to main after
tests, the strict Sphinx build and local-link/download checks. Pull requests build
and verify the site. GitHub Pages must be enabled using the Actions build mode.
The workflow reads the site's current address from GitHub Pages settings, so
switching between the project URL and its custom domain uses the same build.

Successful verification of the selected development branch also requests the
main-branch publisher through ``workflow_run``. Verification has a separate
workflow name to avoid GitHub's self-listener restriction. The hourly refresh
compares both channels' source refs and external revisions. Review the source
refs and workflow branch filters together when changing the development branch.
Public deployment runs on main and publishes both channels in one artifact.

MRIO disaggregation's notification workflow invokes this publication through
``workflow_dispatch``. Configure its ``TUTORIALS_PUBLISH_TOKEN`` repository secret
with a fine-grained token whose selected repository is Tutorials and whose only
additional repository permission is Actions read/write. Its default Metadata
read permission supplies repository identity. Keep that credential in the source
repository's Actions secret store.

The separate ``.github/workflows/refresh.yml`` hourly check also detects changes
in registered external refs and requests publication when the deployed manifest
differs. GitHub can delay scheduled runs and disables schedules on inactive public
repositories. Keep the publisher in its separate push/dispatch workflow so an
inactive schedule cannot disable ordinary publication. Check the Actions history
when auditing refreshes; use the manual publication action for an immediate
rebuild. A frozen workshop edition can select a tag or full commit in the catalogue.

Before merging, inspect the branch rules, PR checks and reviews. After publication,
check the deployed manifest against the intended commits, open representative
public pages and download the notebooks and supporting files. A local preview
does not verify the published site.

Configure a custom domain in GitHub Pages after its DNS CNAME resolves to the
organization's GitHub Pages hostname. Verify the HTTPS certificate and enable
HTTPS enforcement once GitHub has provisioned it. Main MARIO navigation changes
belong in its own documentation migration.
