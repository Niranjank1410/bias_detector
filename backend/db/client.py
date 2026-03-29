"""
Supabase database client.
This module creates a single shared database connection that all 
other modules import and use, rather than everyone creating their own.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# load_dotenv() reads the .env file and loads the variables into
# os.environ so i can access them with os.getenv()
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
	raise EnvironmentError(
		"Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file"
	)

# Create the client once at module level.
# Python caches module imports, so this connection is used only once
# no matter how many files import it.

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
