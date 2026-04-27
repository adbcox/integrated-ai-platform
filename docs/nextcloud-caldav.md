# Nextcloud CalDAV Configuration

## Access

- **Web UI:** https://nextcloud.internal
- **Direct:** http://192.168.10.145:8085
- **Username:** admin
- **Password:** `vault kv get -field=password secret/nextcloud/admin`

## CalDAV Base URL

```
http://192.168.10.145:8085/remote.php/dav/calendars/admin/
```

## Calendars

| Calendar | CalDAV URL |
|----------|-----------|
| Personal | `.../Personal/` |
| Work | `.../work/` |
| Training | `.../training/` |
| Family | `.../family/` |

## Client Setup

### iPhone / iPad

Settings → Calendar → Accounts → Add Account → Other → Add CalDAV Account

- **Server:** `192.168.10.145`
- **User Name:** `admin`
- **Password:** (from Vault)
- **Description:** IAP Calendar

Advanced settings if needed:
- Port: `8085`
- Account URL: `http://192.168.10.145:8085/remote.php/dav`
- Use SSL: Off (or On if using https://nextcloud.internal with CA cert trusted)

### Mac Calendar

Calendar → Add Account → Other CalDAV Account

- **Account Type:** Advanced
- **User Name:** `admin`
- **Password:** (from Vault)
- **Server Address:** `192.168.10.145`
- **Server Path:** `/remote.php/dav/calendars/admin/`
- **Port:** `8085`
- **Use SSL:** No

## Strava Integration

Strava activities are synced automatically to the **training** calendar:

- **Token refresh:** every 30 min via cron (`scripts/refresh-strava-token.sh`)
- **Activity sync:** daily at 06:00 via cron (`scripts/sync-strava-to-calendar.py`)
- **Log files:** `/var/log/strava-refresh.log`, `/var/log/strava-sync.log`

To enable Strava sync, first store OAuth credentials in Vault:

```bash
vault kv put secret/strava/oauth \
  client_id=YOUR_CLIENT_ID \
  client_secret=YOUR_CLIENT_SECRET \
  refresh_token=YOUR_REFRESH_TOKEN
```

Get credentials from: https://www.strava.com/settings/api
