import discord
from discord.ext import commands
import enum
from bot import Vivum

class TranscationType(enum.Enum):
    Revenue = 1
    Expenditure = 2

class TransactionUnit(enum.Enum):
    IndianRupees = 1
    IndianPaise = 2

class Finance(commands.Cog):
    def __init__(self, bot: Vivum):
        self.bot = bot

    @commands.hybrid_group()
    async def finance(self, ctx: commands.Context):
        ...  
    
    @finance.command()
    @discord.app_commands.describe(
        amount="Amount of money to add"
    )
    async def add(
        self, 
        ctx: commands.Context,
        name: str,
        note: str,
        type: TranscationType,
        amount: int,
        units: TransactionUnit | None = None
    ):
        """Adds a record (revenue/expenditure) for your VIVUM department"""
        await ctx.defer(ephemeral=False)
        user = await self.bot.pool.fetchrow("SELECT role_name, is_hod FROM users WHERE user_id = $1", str(ctx.author.id))

        if not user:
            return await ctx.send("You are not assigned to any department. Please ask an admin to assign you to a department")

        if amount < 0:
            return await ctx.send("Amount must be positive. Use 'type' to specify if it is revenue or expenditure")
    
        if not units:
            units = TransactionUnit.IndianRupees

        if units == TransactionUnit.IndianRupees:
            amount *= 100 # Make it paise (1 rupee = 100 paise)
        
        if type == TranscationType.Expenditure:
            amount *= -1
        
        await self.bot.pool.execute(
            """
                INSERT INTO finance_records (
                    user_id,
                    role_name,
                    is_hod,
                    name,
                    note,
                    amount
                )
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(ctx.author.id),
            user["role_name"],
            user["is_hod"],
            name,
            note,
            amount
        )

        await ctx.send("Added record")

async def setup(bot: Vivum):
    await bot.add_cog(Finance(bot))