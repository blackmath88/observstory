# Experiment results: collaboration state

All in `tests/test_coordination.py`, on the synthetic hackathon in `fixtures/collab-lab/`.

| Claim | Result |
|---|---|
| The extractor turns explicit markers into proposed items with their source line, and ignores chatter | Supported (weekday times, next-occurrence times, pr/branch/path/url links, freeze scopes) |
| Nothing becomes declared without a named confirmer | Supported (a blank name is rejected; declared items need `confirmed_by`) |
| Proposed items don't affect reconciliation | Supported |
| Commitment state follows linked work (landed / in progress / not started) | Supported |
| An unstarted commitment raises a cue after half its time has passed | Supported (Dana's evals at Sat 09:30) |
| A freeze that passed while its area kept changing is detected, exactly for pushes and approximately for PRs | Supported (Sat 15:00: `medium` while #12 is open; `high` once it has landed as a commit) |
| A gate passed with committed work still open | Supported (the recorder UI after the web/src freeze) |
| Cues name work, never people, and carry both sides | Supported |
| Cues never enter repository signals | Supported |

Not tested and not claimed: whether real teams confirm items after check-ins (A1); whether freeze cues feel helpful or like policing.
