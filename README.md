# github-ip-lists

Plain-text copies of GitHub's published IP ranges, for firewalls that load a
list from a URL (for example UniFi Network 11 dynamic network lists).

| File (branch `lists`) | Content |
| --- | --- |
| `github-git-v4.txt` | IPv4 ranges from `api.github.com/meta` `.git[]`, one CIDR per line |
| `status.json` | `generated_at` (UTC), source, and entry count |

Raw URL:

```text
https://raw.githubusercontent.com/seanblake/github-ip-lists/lists/github-git-v4.txt
```

A GitHub Action (`.github/workflows/update-lists.yml`) rebuilds the files
daily. The script refuses to publish a list that is short, shrinks by more
than half, or holds a non-public or unusually wide range, so a bad fetch fails
the run instead of changing the firewall.

`main` holds the script and workflow and only changes through a pull request.
The `lists` branch holds the generated data and is written only by the Action.
