"""
🦫 Capybala root proxy module
Ensures `import capybala` resolves immediately both when running from the repo root
and when installed via pip.
"""
from .capybala import *
from .capybala import __version__

