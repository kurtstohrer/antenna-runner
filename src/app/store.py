import os
from enum import Enum 
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseSettings
from apscheduler.schedulers.asyncio import AsyncIOScheduler


scheduler = AsyncIOScheduler(timezone="America/New_York")

class Settings(BaseSettings):
    app_name: str = "Antenna Runner"

class Tags(Enum):
    functions = "functions"
    langs = "langs"

settings = Settings()
tags = Tags



TYPE_MAPPING = {
    "String": str,
    "Bool": bool,
    "Int": int,
    "List": list,
    "Dict": dict,
    "Float": float,
    "Tuple": tuple,
    "Set": set,
    "Bytes": bytes,
}