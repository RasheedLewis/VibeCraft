# Friday Plan

"You need to submit your 3 best videos, a one-page pipeline breakdown, a deployed
link, and a link to your code."

Let's feature-flag sections, because right now, sync + consistency is the focus,
and would work better with a 1-level hierarchy of vid->clips rather than a 2-level
hierarchy vid->sections->clips, and this may have a bit of complexity in
refactoring (idk). Also: my use case is 30-second vids, so let's also support the
user selecting up to 30s from their original clip. After those two pre-requisite
steps, we'll proceed with some character consistency logic, and then some
beat-sync logic, and finally the deliverables.
The consistency + sync approaches are described in High-Level Plan and Technical-Exploration.
