# import os
# import environ

# env = environ.Env()

# BASE_DIR = os.path.dirname(os.path.dirname(
#     os.path.dirname(os.path.abspath(__file__))))
# environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# DEBUG = int(os.environ.get("DEBUG", 1))

# if DEBUG:
#     print("DEBUG: ", DEBUG)
#     print("Development settings")
#     from .development import *
# else:
#     from .production import *

import os
from dotenv import load_dotenv
load_dotenv()

environment = os.getenv('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
else:
    from .development import *