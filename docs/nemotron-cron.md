# Nemotron Cron Job

The Nemotron download is scheduled via cron to run at 00:05 (5 minutes after midnight).

## View Cron Job

```bash
crontab -l | grep download-nemotron
```

## Remove Cron Job

```bash
crontab -l | grep -v download-nemotron | crontab -
```

## Test Manually

```bash
/home/ranj/Project_Chimera/scripts/download-nemotron.sh
```

## Logs

View logs: `tail -f /home/ranj/Project_Chimera/logs/nemotron-download.log`
