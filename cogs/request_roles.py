import logging
from discord.ext import commands
import discord
from bot import Vivum
from config import roles

class RequestModal(discord.ui.Modal, title='Identity'):
    name = discord.ui.TextInput(label='Your Full Name')

    def __init__(self, bot: Vivum, user_id: int, dept: str, is_hod: bool):
        self.bot: Vivum = bot
        self.user_id: int = user_id
        self.dept: str = dept
        self.is_hod: bool = is_hod
        super().__init__(timeout=None)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You cannot accept this request", ephemeral=True)
    
        # Send message to chat channel
        admin_chat = discord.utils.get(self.bot.get_all_channels(), name="admin-chat")

        if not admin_chat:
            logging.error("Backup logs channel not found")
            return await interaction.response.send_message("Internal error: logs channel not found", ephemeral=True)
        
        if not isinstance(admin_chat, discord.TextChannel):
            logging.error("Backup logs channel not a text channel")
            return await interaction.response.send_message("Internal error: logs channel not a text channel", ephemeral=True)

        await admin_chat.send(f"""
@here
        
**New role request for {self.dept}**

User: {interaction.user.mention} ({interaction.user.id})
Name: {self.name.value}
Department: {self.dept}
HOD: {self.is_hod}

Run ``/assign user:{interaction.user.id} name:{self.name.value} dept:{self.dept} hod:{self.is_hod}`` to assign this user to the role.
        """)

        await interaction.response.send_message("Request sent!", ephemeral=True)

class HODView(discord.ui.View):
    def __init__(self, bot: Vivum, user_id: int, dept: str):
        self.bot: Vivum = bot
        self.user_id: int = user_id
        self.dept: str = dept
        super().__init__(timeout=None)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.gray)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You cannot accept this request", ephemeral=True)
    
        await interaction.response.send_modal(RequestModal(self.bot, self.user_id, self.dept, True))

    @discord.ui.button(label="No", style=discord.ButtonStyle.gray)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You cannot accept this request", ephemeral=True)

        await interaction.response.send_modal(RequestModal(self.bot, self.user_id, self.dept, False))

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

        # Ensure user is member
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("You must be a member of the server to request roles", ephemeral=True)
            return

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
        view = RequestRolesPersistentView(ctx.bot)
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