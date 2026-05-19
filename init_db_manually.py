import sys
import os

# Add service/server to path
sys.path.append(os.path.join(os.getcwd(), 'service', 'server'))

from database import init_database
init_database()
print("Database initialized via project logic.")
