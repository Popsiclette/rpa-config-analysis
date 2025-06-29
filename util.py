import os

# Directories
SRC_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
RESOURCE_DIR = BASE_DIR + os.sep + 'resources'

# Files
PROJECTS_FILE = RESOURCE_DIR + os.sep + 'projects_2025_rpa.csv'
REPOS_BY_CODE = RESOURCE_DIR + os.sep + 'projects_2025_rpa_by_code.csv'
REPOS_INTERSECT = RESOURCE_DIR + os.sep + 'projects_2025_rpa_intersect.csv'
REPOS_DETAILS = RESOURCE_DIR + os.sep + 'projects_2025_rpa_by_code_details.csv'