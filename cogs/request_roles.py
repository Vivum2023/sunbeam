from discord.ext import commands
import discord
from bot import Vivum
from config import roles

class HODView(discord.ui.View):
    def __init__(self, bot: Vivum, user_id: int, dept: str):
        self.bot: Vivum = bot
        self.user_id: int = user_id
        self.dept: str = dept
        super().__init__(timeout=None)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.gray)
    async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.gray)
    async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

class RequestRolesPersistentView(discord.ui.View):
    def __init__(self, bot: Vivum):
        self.bot: Vivum = bot
        super().__init__(timeout=None)
        
    @discord.ui.select(
        placeholder="Select a role", 
        min_values=1, 
        max_values=1, 
        custom_id="request_roles:select",
        options=[
            discord.SelectOption(label=name, value=name) for name in roles.keys()
        ]
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if len(select.values) != 1:
            await interaction.response.send_message("You can only select one role", ephemeral=True)
            return
        
        option_selected = select.values[0]

        # Check that option exists
        if not roles.get(option_selected):
            await interaction.response.send_message("Role not found", ephemeral=True)
            return
    
        # Check if user is already assigned to a dept
        row = await self.bot.pool.fetchval("SELECT role_name FROM users WHERE user_id = $1", str(interaction.user.id))

        if row and not (self.bot.config.test_mode and interaction.user.guild_permissions.administrator):
            # Ask if they really want to request a reassignment
            if row == option_selected:
                await interaction.response.send_message("You are already assigned to this department", ephemeral=True)
                return

            return await interaction.response.send_message(f"You are already assigned to another department ({row}). Please DM a 'Admin' role'd user about this?!", ephemeral=True)
        
        return await interaction.response.send_message(
            """
Do you also require the HOD role? 

**Note that you must have been selected (see the spreadsheet) or it WILL be denied!**
        """, 
            ephemeral=True, 
            view=HODView(self.bot, interaction.user.id, option_selected)
        )

class RequestRoles(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot
    
    @commands.hybrid_command()
    async def reqroles(self, ctx: commands.Context):
        """Sends the request roles form"""
        view = RequestRolesPersistentView(ctx)
        msg = await ctx.send(embeds=[
            discord.Embed(
                title="Request Roles",
                description="Note that all role requests will be reviewed by Admins beforehand",
                color=discord.Color.blurple()
            )
            ],
            view=view
        )

async def setup(bot: Vivum):
    bot.add_view(RequestRolesPersistentView(bot))
    await bot.add_cog(RequestRoles(bot))