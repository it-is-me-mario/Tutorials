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
The shared theme's ``partials/versions.html`` supplies a floating bottom-right
control outside the header, with the choices opening upward. Check its fixed
position while scrolling and its keyboard behaviour at narrow widths.

``catalog.json`` owns the tutorial routes, summaries, source repositories and
material lists. Edit each notebook in its listed source repository. The build
creates temporary render and download copies under ``_build``; these copies are
excluded from Git. The source repository's history and original URLs remain the
permanent record.

An optional ``guide`` names an RST explanation from the notebook's source and
revision. The publisher includes a generated ``.rst.inc`` copy in the landing
page and records its hash. Keep the full calculation in the notebook companion.
Set ``guide_includes_downloads`` when the guide places its own Tutorial materials
section. Include ``:download:`` links using the notebook and material basenames,
and a ``:doc:`` link to ``notebook`` for the readable companion. The publisher
then keeps the notebook toctree hidden. The link/download checker verifies the
guide's links and every material hash alongside the rendered notebook.

The shared MARIO theme is imported at the full commit recorded in the catalogue.
Review its templates, CSS, scripts and logo assets together when updating that
commit. ``conf.py`` supplies this site's navigation and search index. The footer
override supplies links to the main MARIO site. ``_static/tutorials.css`` owns
notebook layout adaptations.

The catalogue's ``title`` is used consistently on the index, overview and rendered
notebook. ``category`` supplies the subject label. Do not add a second question
heading above the title. ``partner: cvxlab`` identifies joint tutorials with the
official light/dark logo variants from the shared theme; their provenance is
recorded in ``cvxlab-logo-source.json``. Tutorials belongs inside Resources in
the common header. Keep each card a single native link and retain all source
revision and companion links when changing its layout.

``source_format: mario`` imports a complete worked RST guide and its notebook
from a pinned MARIO commit. The builder removes the source page's title and
metadata, relocates topic/API links to the matching documentation channel and
copies figures from that same commit. Figure hashes are recorded with the guide.
The rendered notebook receives equivalent link/image adjustments; its downloadable
companion preserves every original source cell. Code cells and calculations are
unchanged. The shared theme's ``mario_site`` module supplies only the cards,
steps and disclosure directives, without installing the main site's navigation.
Keep the original documentation addresses working when adding a guide to this
catalogue, and route the Examples index to the corresponding tutorial pages.

Preview is built by the current main-branch publisher, which loads this branch's
committed ``build.py`` and ``conf.py`` presentation and its independent theme pin.
Use that publisher for the complete Latest/Dev/Preview verification and deployment.
Check the seven tutorial overviews, rendered notebooks, figures and companion
downloads together, including the joint logos on light/dark and narrow layouts.

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
For paired tutorials, compare the introductory structure, problem statement,
materials and scenario assumptions with the identified counterpart revision.
Verify reference-share denominators against the model's activity filters and
account for secondary production explicitly. Keep preparation order aligned
between the guide and notebook.

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
