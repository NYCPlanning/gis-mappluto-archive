# MapPLUTO Archive

*******************************

Whenever a new version of MapPLUTO is generated through Data Engineering’s PostGIS data pipeline it must be distributed across many different directories in order to re-source various layers or update associated metadata. This script will pull the generated MapPLUTO data set and distribute it accordingly.

### Prerequisites

A version of Python with the default ArcPy installation that comes with ArcGIS Desktop is required in order to utilize Metadata functionality that is currently not available in the default ArcPy installation that comes with ArcGIS Pro (Python 3). 

##### MapPLUTO_2Web2Prod2Arch2MDrive.py

```
arcpy, os, re, xml, shutil, zipfile, datetime, sys, traceback, ConfigParser
```

### Instructions for running

##### MapPLUTO_2Web2Prod2Arch2MDrive.py

1. Open the script in any integrated development environment (PyCharm is suggested)

2. Ensure that your IDE is set to be utilizing the default version of Python 2 that comes with ArcGIS as its interpreter for this script. This particular python distribution is required for its metadata functionality.

3. Ensure that the Configuration ini file is up-to-date with directory path information.

4. Ensure the correct version strings have been input for prod_version and prev_prod_version on lines 25 and 26, respectively
