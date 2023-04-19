import logging
import os
import asyncpg
import discord
from discord.ext import commands
from loguru import logger
from config import Config

class Vivum(commands.Bot):
    pool: asyncpg.Pool
    config: Config

    def __init__(self, config: Config):
        self.config = config
        super().__init__(
            command_prefix = config.prefix,
            intents=discord.Intents.all()
        )

    async def setup_hook(self):
        logger.info("Called setup_hook")

        self.pool = await asyncpg.create_pool(self.config.database_url)

        try:
            await self.load_extension("jishaku")
        except commands.ExtensionAlreadyLoaded:
            pass

        # For every file in the cogs folder, load it
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                try:
                    logging.info(f"Loading extension {file}...")
                    await self.load_extension(f"cogs.{file[:-3]}")
                except commands.ExtensionAlreadyLoaded:
                    pass
                except Exception as e:
                    logging.info(f"Failed to load extension {file}: {e}")

        logging.info("Ready!")
