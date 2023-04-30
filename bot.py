import logging
import os
import asyncpg
import discord
from discord.ext import commands
import logging
from config import Config, roles
import asyncio

class Vivum(commands.Bot):
    pool: asyncpg.Pool
    config: Config
    roles: dict[str, str]

    def __init__(self, config: Config):
        self.config = config
        super().__init__(
            command_prefix = config.prefix,
            intents=discord.Intents.all(),
            activity=discord.Game(name="cats")
        )

        if not self.config.disabled:
            self.config.disabled = []

        self.roles = roles

    async def setup_db(self):
        logging.info("Setting up database...")
        with open("sql/setup.sql") as f:
            await self.pool.execute(f.read())

    async def setup_hook(self):
        logging.info("Called setup_hook")

        self.pool = await asyncpg.create_pool(self.config.database_url)

        await self.setup_db()

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

        logging.info("Bot setup complete!")

        async def sync_tree():
            logging.info("Starting command tree sync")
            await self.tree.sync()
            logging.info("Synced command tree")

        asyncio.create_task(sync_tree())
    
    async def on_ready(self):
        logging.info("on_ready called")

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        logging.error(f"An error occurred: {error}")
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.CheckFailure):
            return await ctx.send("This command is either disabled or you don't have permission to use it!")

        await ctx.send(f"An error occurred: {error}", ephemeral=True)
        return