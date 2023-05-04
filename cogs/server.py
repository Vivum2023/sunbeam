import asyncio
import logging
import discord
from discord.ext import commands
from cogs.data.layout import ChannelType

from bot import Vivum
from config import roles, protected_roles, protected_cats

class Server(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot
    
    @commands.hybrid_command()
    @commands.is_owner()
    async def buildserver(self, ctx: commands.Context):
        """Builds the servers main comm channels from layout.yaml"""
        if not ctx.guild:
            return await ctx.send("This command can only be used in a guild")

        await ctx.send("Building server channels, please wait...")

        # Delete all channels not in protected_cats
        await ctx.send("**Step 1: Cleanup Channels**")
        for chan in ctx.guild.channels:
            if isinstance(chan, discord.CategoryChannel):
                if chan.name.lower() not in protected_cats:
                    await chan.delete()
                continue

            if chan.category is not None and chan.category.name.lower() in protected_cats:
                continue
            await chan.delete()
        
        # Cleanup roles as well
        await ctx.send("**Step 1.5: Cleanup Roles**")
        for role in ctx.guild.roles:
            if role.name.lower() in protected_roles or role == ctx.guild.default_role:
                continue     

            try:
                await role.delete()
            except Exception as e:
                await ctx.send(f"Failed to delete role {role.name} [cleanup]: {e}, likely normal")

        await ctx.send("**Step 2: Create new roles and channels**")

        hod = await ctx.guild.create_role(
            name="HOD",
            hoist=self.bot.layout.hod_role.hoist,
            permissions=self.bot.layout.hod_role.permissions()
        )

        for name, chan_name in self.bot.roles.items():
            await ctx.send(f"Creating department {name}...")
            role = await ctx.guild.create_role(
                name=name, 
                hoist=self.bot.layout.dept_role.hoist,
                permissions=self.bot.layout.dept_role.permissions()
            )

            for cat_dat in self.bot.layout.categories:
                cat = await ctx.guild.create_category(
                    self.bot.layout.replace_str(
                        cat_dat.name,
                        name=chan_name,
                        label=name
                    ),
                    overwrites=cat_dat.overwrites.construct(
                        ctx.guild.default_role,
                        role,
                        hod
                    ) if cat_dat.overwrites else {}
                )

                for chan in cat_dat.channels:
                    match chan.type:
                        case ChannelType.Text:
                            channel = await ctx.guild.create_text_channel(
                                self.bot.layout.replace_str(
                                    chan.name,
                                    name=chan_name,
                                    label=name
                                ),
                                category=cat,
                                overwrites=chan.overwrites.construct(
                                    ctx.guild.default_role,
                                    role,
                                    hod
                                ) if chan.overwrites else {},
                                topic = self.bot.layout.replace_str(
                                    chan.topic or "",
                                    name=chan_name,
                                    label=name
                                ) if chan.topic else ""
                            )

                            if chan.message:
                                await channel.send(self.bot.layout.replace_str(
                                    chan.message,
                                    name=chan_name,
                                    label=name
                                ))
                        case ChannelType.Voice:
                            await ctx.guild.create_voice_channel(
                                self.bot.layout.replace_str(
                                    chan.name,
                                    name=chan_name,
                                    label=name
                                ),
                                category=cat,
                                overwrites=chan.overwrites.construct(
                                    ctx.guild.default_role,
                                    role,
                                    hod
                                ) if chan.overwrites else {},
                            )

        # Select all user roles
        await ctx.send("**Step 3: Assign roles to users**")

        rows = await self.bot.pool.fetch("SELECT user_id, role_name, name, is_hod FROM users")

        assigned = 1

        for row in rows:
            if assigned % 10 == 0:
                await ctx.send(f"Sleeping for 3 seconds to avoid rl's [{assigned}/{len(rows)}]")
                await asyncio.sleep(3)

            await ctx.send(f"Assigning {row['user_id']} to {row['role_name']} (hod={row['is_hod']}) [{assigned}/{len(rows)}]")
            try:
                user = ctx.guild.get_member(int(row["user_id"]))
                if not user:
                    continue
                
                if not user.nick or user.nick != row["name"]:
                    await user.edit(nick=row["name"], reason="Nickname mismatch")

            except:
                continue

            if not roles.get(row["role_name"]):
                await ctx.send(f"Department {row['role_name']} not found, skipping...")

            role: discord.Role | None = discord.utils.get(ctx.guild.roles, name=row["role_name"])

            if not role:
                continue   

            give_roles = [role]
            if row["is_hod"]:
                give_roles.append(hod)

            await user.add_roles(*give_roles, reason="Rebuilding server")

            assigned += 1

        await ctx.send(f"Assigned {len(rows)} users to their respective departments")

        await ctx.send("**Done!**")

    @commands.hybrid_command()
    @commands.is_owner()
    async def updserver(self, ctx: commands.Context):
        """Updates the server layout to layout.yaml"""
        if not ctx.guild:
            return await ctx.send("This command can only be used in a guild")

        await ctx.send("**Step 1: Preparing**")

        cat_names = []

        for name, chan_name in self.bot.roles.items():
            for cat_dat in self.bot.layout.categories:
                cat_names.append(
                    self.bot.layout.replace_str(
                        cat_dat.name,
                        name=chan_name,
                        label=name
                    )
                )
                
        await ctx.send(f"=> Got expected category list: {cat_names}")

        hod: discord.Role | None = discord.utils.get(ctx.guild.roles, name="HOD")

        if not hod:
            return await ctx.send("FATAL: HOD role not found?")

        await ctx.send("**Step 1: Deleting unexpected categories**")

        deleted = 0
        for chan in ctx.guild.categories:
            if chan.name not in cat_names and chan.name.lower() not in protected_cats:
                await ctx.send(f"=> Deleting category {chan.name}")
                await chan.delete() 
                deleted += 1
        
        await ctx.send(f"=> Deleted {deleted} categories")

        await ctx.send("**Step 2: Checking stuff**")

        chans_covered = []
        for name, chan_name in self.bot.roles.items():
            await ctx.send(f"=> Checking department {name}...")
            role: discord.Role | None = discord.utils.get(ctx.guild.roles, name=name)

            if not role:
                await ctx.send(f"=> Creating non-existent role {name}")
                role = await ctx.guild.create_role(
                    name=name, 
                    hoist=self.bot.layout.dept_role.hoist,
                    permissions=self.bot.layout.dept_role.permissions()
                )

            for cat_dat in self.bot.layout.categories:
                cat: discord.CategoryChannel | None = discord.utils.get(ctx.guild.categories, name=self.bot.layout.replace_str(
                    cat_dat.name,
                    name=chan_name,
                    label=name
                ))

                if not cat:
                    await ctx.send(f"=> Creating non-existent category {self.bot.layout.replace_str(cat_dat.name, name=chan_name, label=name)}")
                    cat = await ctx.guild.create_category(
                        self.bot.layout.replace_str(
                            cat_dat.name,
                            name=chan_name,
                            label=name
                        ),
                        overwrites=cat_dat.overwrites.construct(
                            ctx.guild.default_role,
                            role,
                            hod
                        ) if cat_dat.overwrites else {}
                    )
                else:
                    await ctx.send(f"=> Found category {self.bot.layout.replace_str(cat_dat.name, name=chan_name, label=name)}")

                    ov =  cat_dat.overwrites.construct(
                        ctx.guild.default_role,
                        role,
                        hod
                    ) if cat_dat.overwrites else {}


                    logging.info(f"Overwrites: {ov}")

                    await cat.edit(
                        overwrites=cat_dat.overwrites.construct(
                            ctx.guild.default_role,
                            role,
                            hod
                        ) if cat_dat.overwrites else {}
                    )

                for chan in cat_dat.channels:
                    # Look for channel
                    match chan.type:
                        case ChannelType.Text:
                            c: discord.TextChannel | None = discord.utils.get(cat.text_channels, name=self.bot.layout.replace_str(
                                chan.name,
                                name=chan_name,
                                label=name
                            ))

                            if not c:
                                await ctx.send(f"=> Creating non-existent text channel {self.bot.layout.replace_str(chan.name, name=chan_name, label=name)}")

                                channel = await ctx.guild.create_text_channel(
                                    self.bot.layout.replace_str(
                                        chan.name,
                                        name=chan_name,
                                        label=name
                                    ),
                                    category=cat,
                                    overwrites=chan.overwrites.construct(
                                        ctx.guild.default_role,
                                        role,
                                        hod
                                    ) if chan.overwrites else {},
                                    topic = self.bot.layout.replace_str(
                                        chan.topic or "",
                                        name=chan_name,
                                        label=name
                                    ) if chan.topic else ""
                                )

                                if chan.message:
                                    await channel.send(self.bot.layout.replace_str(
                                        chan.message,
                                        name=chan_name,
                                        label=name
                                    ))
                                
                                chans_covered.append(channel.id)
                            else:
                                # Edit permissions
                                await ctx.send(f"=> Editing permissions for text channel {self.bot.layout.replace_str(chan.name, name=chan_name, label=name)}")

                                args = {
                                    "sync_permissions": True,
                                    "topic": self.bot.layout.replace_str(
                                        chan.topic or "",
                                        name=chan_name,
                                        label=name
                                    ) if chan.topic else ""
                                }

                                if chan.overwrites:
                                    args["overwrites"] = chan.overwrites.construct(
                                        ctx.guild.default_role,
                                        role,
                                        hod
                                    )

                                await c.edit(
                                    **args,
                                )

                                if chan.message:
                                    # Check if message is already sent
                                    if not c.last_message or c.last_message.content != self.bot.layout.replace_str(
                                        chan.message,
                                        name=chan_name,
                                        label=name
                                    ):
                                        # Bulk delete messages if there are any
                                        await ctx.send(f"=> Recreating message for {self.bot.layout.replace_str(chan.name, name=chan_name, label=name)}")
                                        await c.purge(limit=100)

                                        await c.send(self.bot.layout.replace_str(
                                            chan.message,
                                            name=chan_name,
                                            label=name
                                        ))

                                chans_covered.append(c.id)
                        case ChannelType.Voice:
                            cv: discord.VoiceChannel | None = discord.utils.get(cat.voice_channels, name=self.bot.layout.replace_str(
                                chan.name,
                                name=chan_name,
                                label=name
                            ))

                            if not cv:
                                await ctx.send(f"=> Creating non-existent voice channel {self.bot.layout.replace_str(chan.name, name=chan_name, label=name)}")

                                cv = await ctx.guild.create_voice_channel(
                                    self.bot.layout.replace_str(
                                        chan.name,
                                        name=chan_name,
                                        label=name
                                    ),
                                    category=cat,
                                    overwrites=chan.overwrites.construct(
                                        ctx.guild.default_role,
                                        role,
                                        hod
                                    ) if chan.overwrites else {},
                                )

                                chans_covered.append(cv.id)
                            else:
                                args_v = {}

                                args_v["sync_permissions"] = True

                                if chan.overwrites:
                                    args_v["overwrites"] = chan.overwrites.construct(
                                        ctx.guild.default_role,
                                        role,
                                        hod
                                    )

                                await cv.edit(
                                    **args_v
                                )

                                chans_covered.append(cv.id)
                
        await ctx.send("**Step 3: Deleting unexpected channels**")

        for channel in ctx.guild.channels:
            if channel.category and channel.category.name in cat_names and channel.id not in chans_covered:
                await ctx.send(f"=> Deleting unexpected channel {channel.name}")
                await channel.delete(reason="Unexpected channel") 

async def setup(bot: Vivum):
    await bot.add_cog(Server(bot))