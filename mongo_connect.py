
# -*- coding: utf-8 -*-
"""
mrbacco04 copyright

This is a script file.
"""

import logging
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
BAC_LOG = logging.getLogger(__name__)

password = os.getenv("MONGO_PASSWORD", "<wdTWUwfeVRB7aIlD>")
uri = f"mongodb+srv://mrbacco04_db_user:{password}@cluster0.cxzgfix.mongodb.net/?appName=Cluster0"

# Create a new client and connect to the server
BAC_LOG.info("Attempting to connect to MongoDB Atlas")
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    BAC_LOG.info("Successfully connected to MongoDB Atlas, mrbacco!!!")
    
except Exception as e:
    BAC_LOG.error(f"Failed to connect to MongoDB Atlas, mrbacco: {e}")
    
