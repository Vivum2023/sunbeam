from pydantic import BaseModel 

class Config(BaseModel):
    token: str
    prefix: str
    disabled: list[str] | None = None
    database_url: str
    google_drive_backup_folder_id: str

roles = {
    "Logistics": "logistics",
    "Security": "security",
    "Vendor Acquisition": "vendor",
    "Sports": "sports",
    "Dance": "dance",
    "Stage Management": "stage",
    "Finance": "finance",
    "Music": "music",
    "Fun Activities": "fun",
    "Drama": "drama",
    "Registration": "reg",
    "Design": "design",
    "Fundraising": "fundraising",
    "Distribution": "dist",
    "Social Media": "smm",
    "Merchandise": "merch",
}

protected_roles = [
    "sudo",
    "admin",
    "tech support",
    "everyone",
    "l'ordinateur",
    "vc"
]