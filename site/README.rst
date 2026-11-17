Tutorial site maintenance
========================

Sources and ownership
---------------------

``versions.json`` selects content refs for Latest at the root and Dev under
``/dev/``. The publisher reads each catalogue, notebook, guide and material at
the selected commit. Source notebooks remain in their canonical repositories.
Both channels use the publisher's presentation and pinned shared theme.

``versions-manifest.json`` records the publisher and resolved source commits.
Each channel retains its own ``source-manifest.json`` and downloads.
``docs-versions.json`` records HTML pages and anchors for the Latest/Dev selector.
Its native links open each channel home without scripts; a missing counterpart
falls back to that home. The floating control opens upward above the footer.

Preview is retired. Its old HTML routes redirect to their matching Latest page
(or Dev for a Dev-only page), preserving the query string and fragment. These
small redirect pages have no duplicate data or downloads and are excluded from
the channel inventories. Check old links to merged tutorials as well.

``catalog.json`` owns the tutorial routes, summaries, source repositories and
material lists. Edit each notebook in its listed source repository. The build
creates temporary render and download copies under ``_build``; these copies are
excluded from Git. The source repository's history and original URLs remain the
permanent record.

``collections`` combines related source entries into one tutorial page and one
catalogue card. Each part has a heading and stable anchor. Its notebook retains
its original route, source revision and download hash; former overview routes
redirect to the corresponding section. Keep the parts' methods and input years
explicit when they differ. Check the combined explanations, relocated image and
download links, redirects and search entries together.

Use descriptive titles and concrete summaries. Avoid repeating the summary in
an introductory slogan or restating setup instructions after every section.
Keep units, data requirements, attribution and interpretation limits visible.
All channels use the three named authors in ``conf.py`` for their copyright.

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
notebook layout adaptations and the uniform two-column tutorial cards, which
stack on narrow screens.

The catalogue's ``databases`` registry owns source names and optional logo
filenames. Each tutorial lists its database keys; collection cards combine
their members' keys without duplicates. Logos and their credits come from the
pinned shared-theme revision. Keep names visible when no logo is available.
Check each card's source list against its notebooks and inspect wrapping,
logo contrast and the single link per card on desktop and narrow screens.

The tutorial overview's ``Put your hands on`` action opens the source notebook's
GitHub folder so readers can obtain its code and supporting files. Latest uses
main for Tutorials-owned sources. Dev uses its selected source commit, and
external sources follow the catalogue's ref. Verify folder paths with spaces
and repository-root notebooks when changing this action.

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
Check that the last explicit light/dark choice follows those links and is
restored when returning through browser history or to an already open page.
The shared theme owns this preference; do not add a separate site default.

Review all channel homes, a shared tutorial page and any channel-specific exercise.
Check the selector, same-page/anchor switching, fallback, download hashes and
navigation to the corresponding MARIO and Explorer channel. Run the source
calculations separately when changing a notebook. The website build renders
and cleans notebooks without executing their calculations.
For paired tutorials, compare the introductory structure, problem statement,
materials and scenario assumptions with the identified counterpart revision.
Verify reference-share denominators against the model's activity filters and
account for secondary production explicitly. Keep preparation order aligned
between the guide and notebook.

When changing the economy-wide exercise's aggregation, update its workbook,
notebook assertions and guide together. Keep the generation activities required
by its scenarios as individual mapping targets. Execute all three scenarios,
then replace the committed ``results`` directory, summary and downloadable ZIP
from that run. Check CSV coordinates against the exported sets, preserve the
raw flow units and verify the archive contains the same files. The source
EXIOBASE archives stay outside Git. Derived downloads retain their source
attribution and licence.

When publishing the CVXLab input package, maintain its classified sets and
scenario inputs with the notebook's mapping. Execute the optional
``to_cvxlab`` path and inspect written-cell counts for every mapped table,
missing attributes, unmatched coordinates and missing values. Check supplied
unmapped tables by their coordinates and scenario assumptions. Reconstruct
the quantity equations from the resulting workbooks and compare them with the
MARIO reference and scenario outputs. Verify the receiving configuration's
numerical prerequisites separately from data transfer and report any pending
normalization or solve requirement. Include the original configuration's
licence and the derived data's source notices in the downloadable package.

Known zero matrices can be omitted from the exercise's explicit CSV list.
Review that list, the committed files, archive and guide together. Preserve
zero blocks required inside a populated receiving table's coordinate domain.

Publication and external refreshes
---------------------------------

The workflow in ``.github/workflows/pages.yml`` publishes pushes to main after
tests, the strict Sphinx build and local-link/download checks. Pull requests build
and verify the site. GitHub Pages must be enabled using the Actions build mode.
The workflow reads the site's current address from GitHub Pages settings, so
switching between the project URL and its custom domain uses the same build.

The hourly refresh compares the channels' source refs and external revisions.
Public deployment runs on main and publishes all channels in one artifact.
After promoting feature work, channels can share main until another content
ref is selected. Before deleting integrated branches, update every channel
ref and any branch-specific workflow triggers that still refer to them.
Verify the merged ancestry, then check the public manifests and a manual
publication after deletion so refreshes continue using existing refs.

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
