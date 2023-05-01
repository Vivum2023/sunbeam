import pydantic
import enum
import discord

class Role(pydantic.BaseModel):
    perms: dict[str, bool]
    hoist: bool

    def permissions(self) -> discord.Permissions:
        return discord.Permissions(**self.perms)

class DeptRole(enum.Enum):
    Everyone = "everyone"
    Dept = "dept"
    Hod = "hod"

    def match(self, everyone: discord.Role, dept_role: discord.Role, hod_role: discord.Role) -> discord.Role:
        if self == DeptRole.Everyone:
            return everyone
        elif self == DeptRole.Dept:
            return dept_role
        elif self == DeptRole.Hod:
            return hod_role
        else:
            raise ValueError("Invalid DeptRole")

class ChannelType(enum.Enum):
    Text = "text"
    Voice = "voice"

class Overwrite(pydantic.BaseModel):
    __root__: dict[DeptRole, dict[str, bool]]

    def construct(
        self,
        everyone: discord.Role, 
        dept_role: discord.Role, 
        hod_role: discord.Role
    ) -> dict[discord.Role | discord.Member, discord.PermissionOverwrite]:
        if not self.__root__:
            return {}

        overwrites = {}

        done_keys = []

        for key, perms in self.__root__.items():
            role = key.match(everyone, dept_role, hod_role)

            if role in done_keys:
                raise ValueError(f"Duplicate role {role} in perm overwrites")
            
            done_keys.append(role)

            overwrites[role] = discord.PermissionOverwrite(**perms)

        return overwrites

class Channel(pydantic.BaseModel):
    name: str
    type: ChannelType
    topic: str | None = None
    overwrites: Overwrite | None = None
    message: str | None = None

class Category(pydantic.BaseModel):
    name: str
    overwrites: Overwrite | None = None
    channels: list[Channel]

class Layout(pydantic.BaseModel):
    # HOD Role
    hod_role: Role

    # Dept role
    dept_role: Role
    
    # Category list
    categories: list[Category]

    def replace_str(self, orig: str, *, name: str, label: str) -> str:
        return orig.replace("$name", name).replace("$label", label)