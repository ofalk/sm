import os
from sm.settings import TEMPLATES
path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATES[0]['DIRS'].append(path)
