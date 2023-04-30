import json
import discord
from discord.ext import commands, tasks

from bot import Vivum

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
import logging
import tempfile
import subprocess
from googleapiclient.http import MediaFileUpload
from datetime import datetime

GIVE_PERMS_ANYONE = False

class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

class Backups(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot

        # Look for servacc.json, otherwise disable this cog
        try:
            with open("servacc.json") as f:
                self.servacc = json.load(f)
        except FileNotFoundError:
            logging.warn("servacc.json not found, disabling backups")
            self.servacc = None
        
        self.service_credentials = None
        self.gscopes = ["https://www.googleapis.com/auth/drive"]
        self.gservice = None
        if self.servacc:
            self.service_credentials = service_account.Credentials.from_service_account_info(
                self.servacc,
                scopes=self.gscopes
            )

            # Create a new client
            self.gservice = build('drive', 'v3', credentials=self.service_credentials, cache=MemoryCache())

        self.backup.start()

    @tasks.loop(hours=2)
    async def backup(self):
        if not self.gservice:
            return

        log_channel = discord.utils.get(self.bot.get_all_channels(), name="backup-logs")

        if not log_channel:
            logging.error("Backup logs channel not found")
            return
        
        logging.info("Starting backup...")

        # Create temp file
        try:
            tf = tempfile.NamedTemporaryFile()
        except Exception as e:
            logging.error(f"Failed to create temp file: {e}")
            return
        
        logging.info(f"Created temp file: {tf.name}")

        # Call pg_dump -Fc --no-owner -d vivum -f tf.name
        try:
            rc = subprocess.call(
                [
                    "pg_dump",
                    "-Fc",
                    "--no-owner",
                    "-d",
                    "vivum",
                    "-f",
                    tf.name
                ]
            )

            if rc != 0:
                logging.error(f"pg_dump failed with return code {rc}")
                return
            
        except Exception as e:
            logging.error(f"Failed to dump database: {e}")
            return
        
        logging.info("Saving dumped db to drive...")

        # Upload to drive
        try:
            file_metadata = {
                "name": f"VIVUM_BACKUP_{datetime.now().strftime('%m/%d/%Y-%H:%M:%S')}.dump",
                "parents": [self.bot.config.google_drive_backup_folder_id]
            }

            media = MediaFileUpload(tf.name)
            
            file = self.gservice.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()

            logging.info(f"Uploaded file to drive with id {file.get('id')}")

            # Create permissions
            if GIVE_PERMS_ANYONE:
                perms = self.gservice.permissions().create(
                    fileId=file.get("id"),
                    body={
                        "role": "reader",
                        "type": "anyone"
                    }
                ).execute()

                logging.info(f"Created permissions for file {file.get('id')}: {perms}")

            # Get file link
            file_link = self.gservice.files().get(
                fileId=file.get("id"),
                fields="webViewLink"
            ).execute()

            logging.info(f"Got file link: {file_link.get('webViewLink')}")

            # Send message to log channel
            await log_channel.send(
                f"Backup complete at {datetime.now()}! Uploaded to drive with id {file.get('id')}.\n\n{file_link.get('webViewLink')}",
                suppress_embeds=True
            )

        except Exception as e:
            logging.error(f"Failed to upload file to drive: {e}")
            return
        
    @backup.before_loop
    async def before_backup(self):
        await self.bot.wait_until_ready()

async def setup(bot: Vivum):
    await bot.add_cog(Backups(bot))