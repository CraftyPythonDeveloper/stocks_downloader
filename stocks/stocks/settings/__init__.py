import os

from .base import *

if os.environ.get("stocks") == "prod":
    from .prod import *
else:
    from .dev import *
