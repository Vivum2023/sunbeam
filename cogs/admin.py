import discord
from discord.ext import commands

from bot import Vivum
from config import roles, protected_roles

class Admin(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot

    @commands.hybrid_command()
    @commands.has_guild_permissions(administrator=True)
    @discord.app_commands.choices(
        dept=[
            discord.app_commands.Choice(name=name, value=name) for name in roles.keys()
        ]
    )
    async def assign(
        self, 
        ctx: commands.Context, 
        user: discord.Member, 
        dept: str, 
        hod: bool,
        reassign: bool = False
    ):
        await ctx.defer(ephemeral=False)

        if reassign:
            # Delete from DB
            await self.bot.pool.execute("DELETE FROM user_roles WHERE user_id = $1", str(user.id))

            # Remove all roles
            roles_to_rem = []
            for role in user.roles:
                if role.name.lower() not in protected_roles:
                    roles_to_rem.append(role)
            
            await user.remove_roles(*roles_to_rem, reason="Reassigning user department")

        # Find HOD role by name
        hod_role: discord.Role = discord.utils.get(ctx.guild.roles, name="HOD")

        if not hod_role:
            return await ctx.send("HOD role not found on discord")
        
        if not roles.get(dept):
            return await ctx.send(f"Department {dept} not found")

        role: discord.Role = discord.utils.get(ctx.guild.roles, name=dept)

        if not role:
            return await ctx.send("Role not found on discord")
        
        # Check db to see if a user is alr in another dept
        row = await self.bot.pool.fetchval("SELECT role_name FROM user_roles WHERE user_id = $1", str(user.id))

        if row and row != dept:
            return await ctx.send(f"User is already in another department ({row}). Set ``reassign`` to True to change a users department or HOD status.")

        # Save to DB
        await self.bot.pool.execute("INSERT INTO user_roles VALUES ($1, $2, $3)", str(user.id), dept, hod)    

        if hod:
            give_roles = [role, hod_role]
        else:
            give_roles = [role]
        
        await user.add_roles(*give_roles, reason=f"Dept assigned: {dept} (hod={hod})")

        await ctx.send(f"Assigned {user.mention} to {dept} department, hod={hod}", allowed_mentions=None)

    @commands.hybrid_command()
    @commands.is_owner()
    async def buildserver(self, ctx: commands.Context):
        await ctx.send("Building server channels, please wait...")

        protected_cats = [
            "information",
            "general",
            "admin"
        ]

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

        hod = await ctx.guild.create_role(name="HOD")

        for name, chan_name in self.bot.roles.items():
            await ctx.send(f"Creating department {name}...")
            role = await ctx.guild.create_role(name=name, hoist=True)

            cat = await ctx.guild.create_category(name, overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=False,
                    connect=False
                ),
                hod: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=False,
                    connect=False
                ),
                role: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    connect=True
                ),
                
            })
            your_dep = await ctx.guild.create_text_channel(f"in-{chan_name}", category=cat, overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            })

            await your_dep.send(f"If you can see this channel, it means that you are a part of the '{name}' department!")

            await ctx.guild.create_text_channel(chan_name, category=cat)
            await ctx.guild.create_voice_channel(name, category=cat)
            await ctx.guild.create_text_channel(f"{chan_name}-input", category=cat, overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            })

        # Select all user roles
        await ctx.send("**Step 3: Assign roles to users**")

        rows = await self.bot.pool.fetch("SELECT user_id, role_name, is_hod FROM user_roles")

        assigned = 1

        for row in rows:
            if assigned % 10 == 0:
                await ctx.send(f"Sleeping for 3 seconds to avoid rl's [{assigned}/{len(rows)}]")

            await ctx.send(f"Assigning {row['user_id']} to {row['role_name']} (hod={row['is_hod']}) [{assigned}/{len(rows)}]")
            try:
                user = ctx.guild.get_member(int(row["user_id"]))
                if not user:
                    continue
            except:
                continue

            if not roles.get(row["role_name"]):
                await ctx.send(f"Department {row['role_name']} not found, skipping...")

            role: discord.Role = discord.utils.get(ctx.guild.roles, name=row["role_name"])

            if not role:
                continue   

            give_roles = [role]
            if row["is_hod"]:
                hod_role: discord.Role = discord.utils.get(ctx.guild.roles, name="HOD")
                give_roles.append(hod_role)

            await user.add_roles(*give_roles, reason="Rebuilding server")

            assigned += 1

        await ctx.send(f"Assigned {len(rows)} users to their respective departments")

        await ctx.send("**Done!**")
async def setup(bot: Vivum):
    await bot.add_cog(Admin(bot))