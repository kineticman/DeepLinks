# Cron Examples

Set once at the top of your crontab:
```
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/home/<user>
MAILTO=""
CRON_TZ=America/New_York
```

The scripts assume a repo at `/home/<user>/Projects/DeepLinks`.

### DeepLinks hourly refresh (guarded with flock)
```
0 * * * * /usr/bin/flock -n /tmp/deeplinks_hourly.lock bash -lc "cd /home/<user>/Projects/DeepLinks && /bin/bash /home/<user>/Projects/DeepLinks/hourly.sh" >> /home/<user>/Projects/DeepLinks/logs/hourly.log 2>&1
```

### DeepLinks nightly scrape @ 03:30 (guarded with flock)
```
30 3 * * * /usr/bin/flock -n /tmp/deeplinks_nightly.lock bash -lc "cd /home/<user>/Projects/DeepLinks && /bin/bash /home/<user>/Projects/DeepLinks/nightly_scrape.sh" >> /home/<user>/Projects/DeepLinks/logs/nightly.log 2>&1
```

Notes:
- `hourly.sh` changes to its own directory and exports `DEEPLINKS_DB` to avoid CWD/DB path issues.
- Both entries `cd` into the repo so relative paths resolve correctly.
