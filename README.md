# Vivum 23 Discord Bot

## Setup Bot

1. Install postgres 14+
2. Create a database called vivum: ``CREATE DATABASE vivum;``
3. Create a Google Cloud Platform project, then enable "Google Drive API" and then lastly, create a service account and download the credentials file. Create a folder on your own Google Drive and share it with the service account email, copy the folder ID from the URL of the folder created and paste it in the config file as the "google_drive_backup_folder_id" value.

## Setup API

The API requires deployproxy to be installed and configured: https://github.com/infinitybotlist/deployproxy

Sample deploy code for deployproxy:

```yaml
  vivum.botlist.app:
    url: "https://vivum.botlist.app"
    description: VIVUM
    enabled: true
    to: http://localhost:49104
    strict: true # Strict means that the permissive allowlist is ignored
    hide_login_html: true
```