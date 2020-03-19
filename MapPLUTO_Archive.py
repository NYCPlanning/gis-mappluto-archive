# Must be run with ArcPy Python27 32-bit version

import os, re, xml.etree.ElementTree as ET, arcpy, shutil, zipfile, datetime, sys, traceback, ConfigParser
from zipfile import ZipFile

# Get user input on version number. --------------------------------------------------------------------

try:
    config = ConfigParser.ConfigParser()
    config.read(r'MapPLUTO_config_sample.ini')
    log_path = config.get('PATHS', 'Log_Path')
    log = open(log_path, "a")
    StartTime = datetime.datetime.now().replace(microsecond=0)

    # Assign path variables. ---------------------------------------------------------------------------

    sde_prod_env = config.get('PATHS', 'PROD_SDE_Path')
    sde_arch_env = config.get('PATHS', 'Archive_SDE_Path')
    bytes_env = config.get('PATHS', 'Bytes_Path')
    temp_env = config.get('PATHS', 'Temp_Path')
    m_path = config.get('PATHS', 'M_Path')
    m_bldg_path = config.get('PATHS', 'M_Bldg_Path')
    m_arch_path = config.get('PATHS', 'M_Archive_Path')
    today_dt = datetime.datetime.now()
    today = today_dt.strftime('%m_%d_%Y')
    prod_version = '20v2'
    prev_prod_version = '20v1'

    # Check Bytes directory for version dir -------------------------------------------------------------

    bytes_dirs = ['csv', 'fgdb', 'meta', 'raw_data', 'shapefiles', 'web']

    dir_list = []

    for item in os.listdir(temp_env):
        dir_list.append(item)
        print(dir_list)

    m_bytes_version_path = os.path.join(temp_env, prod_version)

    print("Checking if version directory needs to be generated.")
    if prod_version not in dir_list:
        os.mkdir(m_bytes_version_path)
    else:
        print("Version directory already exists.")

    # Check Bytes version directory for desired template subdirs -----------------------------------------

    print("Parsing {} directory for appropriate template sub-directories".format(prod_version))
    for subdir in bytes_dirs:
        if os.path.exists(os.path.join(m_bytes_version_path, subdir)):
            print("{} folder already exists. Skipping".format(subdir))
        else:
            os.mkdir(os.path.join(m_bytes_version_path, subdir))

    # Check if archive directory exists in web dir

    if os.path.exists(os.path.join(m_bytes_version_path, 'web', 'archive')):
        print("Archive folder already exists. Skipping generation")
    else:
        os.mkdir(os.path.join(m_bytes_version_path, 'web', 'archive'))

    # Check if MapPLUTO raw_data location exists

    if os.path.exists(os.path.join(m_bytes_version_path, 'raw_data')):
        print('Raw data folder found')
        raw_data_path = os.path.join(m_bytes_version_path, 'raw_data')
    else:
        print("No Raw data folder for found. Aborting script.".format(prod_version))

    # Check MapPLUTO raw_data location for csv and csv directory requisite files and move them -------------------------

    m_bytes_prod_csv = os.path.join(m_bytes_version_path, 'csv')

    desired_csv_files = ['pluto.csv', 'PLUTOChangeFile{}.csv'.format(prod_version)]

    desired_pdf_csv_files = ['PLUTOChangeFileReadme{}.pdf'.format(prod_version),
                         'PLUTODD{}.pdf'.format(prod_version),
                         'PlutoReadme{}.pdf'.format(prod_version)]

    print("Parsing raw data directory for CSV and PDF files")
    for f in os.listdir(raw_data_path):
        print(os.path.join(raw_data_path, f))
        print(os.path.join(m_bytes_prod_csv, f))
        if f in desired_csv_files:
            if os.path.exists(os.path.join(m_bytes_prod_csv, f)):
                print("{} already exists in output directory. Skipping".format(f))
            else:
                print("Raw csv file found. Moving to csv directory")
                shutil.copyfile(os.path.join(raw_data_path, f),
                                os.path.join(m_bytes_prod_csv, f))
                if prod_version not in f:
                    os.rename(os.path.join(m_bytes_prod_csv, f),
                              os.path.join(m_bytes_prod_csv, '{}_{}.csv'.format(f.split('.')[0], prod_version)))
        if f in desired_pdf_csv_files:
            if os.path.exists(os.path.join(m_bytes_prod_csv, f)):
                print("{} already exists in output directory. Skipping".format(f))
            else:
                print("PDF metadata files found. Moving to csv directory")
                shutil.copyfile(os.path.join(raw_data_path, f),
                                os.path.join(m_bytes_prod_csv, f))

    # Zip csv files --------------------------------------------------------------------------------------------------

    desired_csv_zip_files = [
                             'pluto_{}.csv'.format(prod_version),
                             'PLUTODD{}.pdf'.format(prod_version),
                             'PlutoReadme{}.pdf'.format(prod_version),
                             ]

    desired_change_zip_files = ['PLUTOChangeFileReadme{}.pdf'.format(prod_version),
                                'PLUTOChangeFile{}.csv'.format(prod_version)]

    print("Creating csv zips")
    pluto_csv_path = os.path.join(m_bytes_prod_csv, 'nyc_pluto_{}_csv.zip'.format(prod_version))
    pluto_change_path = os.path.join(m_bytes_prod_csv, 'PLUTOChangeFile{}.zip'.format(prod_version))
    pluto_csv_zip_path = zipfile.ZipFile(os.path.join(m_bytes_prod_csv, 'nyc_pluto_{}_csv.zip'.format(prod_version)), mode='w')
    pluto_change_zip_path = zipfile.ZipFile(os.path.join(m_bytes_prod_csv, 'PLUTOChangeFile{}.zip'.format(prod_version)), mode='w')

    if os.path.exists(pluto_csv_path):
        print("Beginning to zip requisite csv directory files for csv path")
        os.chdir(m_bytes_prod_csv)
        for f in os.listdir(m_bytes_prod_csv):
            if f in desired_csv_zip_files:
                pluto_csv_zip_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
        pluto_csv_zip_path.close()
        print("Zipping of csv requisite files complete.")
    else:
        print("Missing requisite zip file")

    if os.path.exists(pluto_change_path):
        print("Beginning to zip requisite csv directory files for change path")
        os.chdir(m_bytes_prod_csv)
        for f in os.listdir(m_bytes_prod_csv):
            if f in desired_change_zip_files:
                pluto_change_zip_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
        pluto_change_zip_path.close()
        print("Zipping of csv change requisite files complete.")
    else:
        print("Missing requisite change zip file")


    # Export metadata to BytesProduction directory using old MapPLUTO Production source -------------------------------
    print("Beginning requisite metadata file copy")
    Arcdir = arcpy.GetInstallInfo("desktop")["InstallDir"]
    translator = Arcdir + "Metadata/Translator/ARCGIS2FGDC.xml"

    sde_prod_clip_meta = config.get('PATHS', 'MapPLUTO_SDE_Clipped_Path')
    sde_prod_unclip_meta = config.get('PATHS', 'MapPLUTO_SDE_Unclipped_Path')
    m_bytes_prod_meta = os.path.join(temp_env, prod_version, 'meta')

    if os.path.exists(os.path.join(m_bytes_prod_meta, 'PLUTOmeta.xml')):
        print("PLUTO meta already exists in BytesProduction. Skipping")
    else:
        print("Exporting MapPLUTO clipped metadata files to BytesProduction meta folders")
        arcpy.ExportMetadata_conversion(sde_prod_clip_meta,
                                        translator,
                                        os.path.join(m_bytes_prod_meta, 'PLUTOmeta.xml'))

    if os.path.exists(os.path.join(m_bytes_prod_meta, 'PLUTOmeta_unclip.xml')):
        print("PLUTO unclipped meta already exists in BytesProduction. Skipping")
    else:
        print("Exporting MapPLUTO unclipped metadata files to BytesProduction meta folder")
        arcpy.ExportMetadata_conversion(sde_prod_unclip_meta,
                                        translator,
                                        os.path.join(m_bytes_prod_meta, 'PLUTOmeta_unclip.xml'))

    # Modify existing xml fields to update metdata -------------------------------------------------------------------

    print(m_bytes_prod_meta)

    def replace_xml_content(input):
        print("Writing new metadata info to xml exports")
        tree = ET.parse(os.path.join(m_bytes_prod_meta, input))
        root = tree.getroot()
        print("Writing publication date to {}".format(tree))
        for item in root.iter("pubdate"):
            item.text = str(today)
        print("Writing edition")
        for item in root.iter("edition"):
            item.text = str(prod_version)
        print("Writing issue")
        for item in root.iter("issue"):
            item.text = "MapPLUTO {}".format(prod_version)
        print("Writing title")
        for item in root.iter("title"):
            item.text = "New York City, MapPLUTO {}".format(prod_version)
        print("Write dataset version")
        for item in root.getiterator():
            try:
                item.text = item.text.replace(prev_prod_version, prod_version)
            except AttributeError:
                pass
        print("Overwriting initial output with in-memory modifications")
        tree.write(os.path.join(m_bytes_prod_meta, input))
        print("Done")

    if os.path.exists(os.path.join(m_bytes_prod_meta, 'PLUTOmeta.xml')):
        replace_xml_content("PLUTOmeta.xml")

    if os.path.exists(os.path.join(m_bytes_prod_meta, 'PLUTOmeta_unclip.xml')):
        replace_xml_content("PLUTOmeta_unclip.xml")

    # Export metadata pdfs to shapefile directory ------------------------------------------------------------------
    m_bytes_prod_shape = os.path.join(temp_env, prod_version, 'shapefiles')

    desired_csv_pdf_shp_files = ['PLUTODD{}.pdf'.format(prod_version),
                                 'PlutoReadme{}.pdf'.format(prod_version),
                                 'PLUTOChangeFileReadme{}.pdf'.format(prod_version),
                                 'PLUTOChangeFile{}.csv'.format(prod_version)]

    print("Exporting necessary metadata files to shapefile directory")
    for f in os.listdir(raw_data_path):
        if f in desired_csv_pdf_shp_files:
            print(os.path.join(raw_data_path, f))
            print(os.path.join(m_bytes_prod_shape, f))
            shutil.copyfile(os.path.join(raw_data_path, f),
                            os.path.join(m_bytes_prod_shape, f))

    # Export standard shapefiles to Bytes Production ----------------------------------------------------------------

    print("Setting environment workspace for shapefile export")
    arcpy.env.workspace = raw_data_path
    output_gdb_list = arcpy.ListWorkspaces('*', 'FileGDB')
    print("Beginning shapefile export steps")
    if os.path.exists(os.path.join(raw_data_path, 'MapPLUTO_{}_clipped.gdb'.format(prod_version))) \
            and os.path.exists(os.path.join(raw_data_path, 'MapPLUTO_{}_unclipped.gdb'.format(prod_version))):
        if not os.path.exists(os.path.join(m_bytes_prod_shape, 'MapPLUTO_UNCLIPPED.shp'.format(prod_version))):
            for fgdb in output_gdb_list:
                print("MapPLUTO unclipped Shapefile exports not found. Parsing for availability")
                if 'unclipped' in fgdb:
                    gdb_env = os.path.join(raw_data_path, fgdb)
                    arcpy.env.workspace = gdb_env
                    fgdb_avail = arcpy.ListFeatureClasses()
                    arcpy.env.workspace = m_bytes_prod_shape
                    arcpy.env.overwriteOutput = True
                    for item in fgdb_avail:
                            print("Exporting MapPLUTO unclipped shapefiles to BytesProduction shapefile directory.")
                            arcpy.FeatureClassToFeatureClass_conversion(os.path.join(raw_data_path, fgdb, item),
                                                                        m_bytes_prod_shape, 'MapPLUTO_UNCLIPPED')
        if not os.path.exists(os.path.join(m_bytes_prod_shape, 'MapPLUTO.shp')):
            for fgdb in output_gdb_list:
                print("MapPLUTO clipped Shapefile exports not found. Parsing for availability")
                if 'clipped' in fgdb:
                    gdb_env = os.path.join(raw_data_path, fgdb)
                    arcpy.env.workspace = gdb_env
                    fgdb_avail = arcpy.ListFeatureClasses()
                    arcpy.env.workspace = m_bytes_prod_shape
                    arcpy.env.overwriteOutput = True
                    for item in fgdb_avail:
                            print("Exporting MapPLUTO clipped shapefile to BytesProduction shapefile directory")
                            arcpy.FeatureClassToFeatureClass_conversion(os.path.join(raw_data_path, fgdb, item),
                                                                        m_bytes_prod_shape, 'MapPLUTO')
    else:
        print("Missing one or both of the input feature classes. Aborting script")
        sys.exit()

    # Zip shapefile exports -------------------------------------------------------------------------------------------

    print("Zipping shapefile exports")
    m_bytes_prod_archive = os.path.join(m_bytes_version_path, 'web', 'archive')

    shp_zip_path = zipfile.ZipFile(os.path.join(m_bytes_prod_shape, 'nyc_mappluto_{}_shp.zip'.format(prod_version)), mode='w')
    shp_zip_unclipped_path = zipfile.ZipFile(os.path.join(m_bytes_prod_shape, 'nyc_mappluto_{}_unclipped_shp.zip'.format(prod_version)), mode='w')
    shp_arc_zip_path = zipfile.ZipFile(os.path.join(m_bytes_prod_archive, 'nyc_mappluto_{}_arc_shp.zip'.format(prod_version)), mode='w')
    shp_arc_zip_change_path = zipfile.ZipFile(os.path.join(m_bytes_prod_archive, 'nyc_mappluto_{}_arc_w_chg_shp.zip'.format(prod_version)), mode='w')

    shp_zip_files = ['MapPLUTO', 'PLUTODD{}'.format(prod_version), 'PlutoReadme{}'.format(prod_version)]
    shp_zip_unclipped_files = ['MapPLUTO_UNCLIPPED', 'PLUTODD{}'.format(prod_version), 'PlutoReadme{}'.format(prod_version)]
    shp_arc_files = ['MapPLUTO', 'MapPLUTO_UNCLIPPED', 'PLUTODD{}'.format(prod_version), 'PlutoReadme{}'.format(prod_version)]
    shp_arc_chg_files = ['MapPLUTO', 'MapPLUTO_UNCLIPPED', 'PLUTOChangeFile{}'.format(prod_version),
                         'PLUTOChangeFileReadme{}'.format(prod_version), 'PLUTODD{}'.format(prod_version),
                         'PlutoReadme{}'.format(prod_version)]

    os.chdir(m_bytes_prod_shape)
    for f in os.listdir(m_bytes_prod_shape):
        if f.split('.')[0] in shp_arc_chg_files:
            shp_arc_zip_change_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Change archive shapefile zip".format(f))
        if f.split('.')[0] in shp_arc_files:
            shp_arc_zip_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Archive shapefile zip".format(f))
        if f.split('.')[0] in shp_zip_files:
            shp_zip_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Clipped shapefile zip".format(f))
        if f.split('.')[0] in shp_zip_unclipped_files:
            shp_zip_unclipped_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Unclipped shapefile zip".format(f))

    # Export metadata pdfs to fgdb directory ------------------------------------------------------------------
    m_bytes_prod_fgdb = os.path.join(temp_env, prod_version, 'fgdb')

    desired_csv_pdf_fgdb_files = ['PLUTODD{}.pdf'.format(prod_version),
                                 'PlutoReadme{}.pdf'.format(prod_version),
                                 'PLUTOChangeFileReadme{}.pdf'.format(prod_version),
                                 'PLUTOChangeFile{}.csv'.format(prod_version)]

    print("Exporting necessary metadata files to shapefile directory")
    for f in os.listdir(raw_data_path):
        if f in desired_csv_pdf_fgdb_files:
            shutil.copyfile(os.path.join(raw_data_path, f),
                            os.path.join(m_bytes_prod_fgdb, f))

    # Export fgdbs and zipped fgdbs to Bytes Production -----------------------------------
    print("Beginning fgdb export")
    m_bytes_prod_fgdb = os.path.join(temp_env, prod_version, 'fgdb')

    if os.path.exists(os.path.join(raw_data_path, 'MapPLUTO_{}_clipped.gdb'.format(prod_version))) \
            and os.path.exists(os.path.join(raw_data_path, 'MapPLUTO_{}_unclipped.gdb'.format(prod_version))):
        if not os.path.exists(os.path.join(m_bytes_prod_fgdb, 'MapPLUTO_{}.gdb'.format(prod_version))):
            for fgdb in output_gdb_list:
                print(fgdb)
                if 'clipped' in fgdb:
                    print("Copying clipped fgdb dataset")
                    arcpy.Copy_management(fgdb, os.path.join(m_bytes_prod_fgdb, 'MapPLUTO_{}.gdb'.format(prod_version)))
        if not os.path.exists(os.path.join(m_bytes_prod_fgdb, 'MapPLUTO_{}_unclipped.gdb'.format(prod_version))):
            for fgdb in output_gdb_list:
                print(fgdb)
                if 'unclipped' in fgdb:
                    print("Copying unclipped fgdb dataset")
                    arcpy.Copy_management(fgdb, os.path.join(m_bytes_prod_fgdb, 'MapPLUTO_{}_unclipped.gdb'.format(prod_version)))

    # Zip fgdb exports ------------------------------------------------------------------------------------------------

    print("Zipping fgdb exports")

    fgdb_zip_path = zipfile.ZipFile(os.path.join(m_bytes_prod_fgdb, 'nyc_mappluto_{}_fgdb.zip'.format(prod_version)),
                                   mode='w')
    fgdb_zip_unclipped_path = zipfile.ZipFile(
        os.path.join(m_bytes_prod_fgdb, 'nyc_mappluto_{}_unclipped_fgdb.zip'.format(prod_version)), mode='w')
    fgdb_arc_zip_path = zipfile.ZipFile(
        os.path.join(m_bytes_prod_archive, 'nyc_mappluto_{}_arc_fgdb.zip'.format(prod_version)), mode='w')
    fgdb_arc_zip_change_path = zipfile.ZipFile(
        os.path.join(m_bytes_prod_archive, 'nyc_mappluto_{}_arc_w_chg_fgdb.zip'.format(prod_version)), mode='w')

    fgdb_zip_files = ['MapPLUTO_{}'.format(prod_version), 'PLUTODD{}'.format(prod_version), 'PlutoReadme{}'.format(prod_version)]

    fgdb_zip_unclipped_files = ['MapPLUTO_{}_unclipped'.format(prod_version), 'PLUTODD{}'.format(prod_version),
                               'PlutoReadme{}'.format(prod_version)]

    fgdb_arc_files = ['MapPLUTO_{}'.format(prod_version), 'MapPLUTO_{}_unclipped'.format(prod_version),
                     'PLUTODD{}'.format(prod_version), 'PlutoReadme{}'.format(prod_version)]

    fgdb_arc_chg_files = ['MapPLUTO_{}'.format(prod_version), 'MapPLUTO_{}_unclipped'.format(prod_version),
                         'PLUTOChangeFile{}'.format(prod_version), 'PLUTOChangeFileReadme{}'.format(prod_version),
                         'PLUTODD{}'.format(prod_version), 'PlutoReadme{}'.format(prod_version)]

    os.chdir(m_bytes_prod_fgdb)
    for f in os.listdir(m_bytes_prod_fgdb):
        if f.split('.')[0] in fgdb_arc_chg_files:
            fgdb_arc_zip_change_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Change archive shapefile zip".format(f))
        if f.split('.')[0] in fgdb_arc_files:
            fgdb_arc_zip_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Archive shapefile zip".format(f))
        if f.split('.')[0] in fgdb_zip_files:
            fgdb_zip_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Clipped shapefile zip".format(f))
        if f.split('.')[0] in fgdb_zip_unclipped_files:
            fgdb_zip_unclipped_path.write(f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to Unclipped shapefile zip".format(f))
    print("Zipping complete")

    # Export all zips to web directory
    print("Copying all zips to web directory")
    m_bytes_prod_web = os.path.join(temp_env, prod_version, 'web')

    for dir in bytes_dirs:
        if dir is not 'web':
            zip_folder_path = os.path.join(temp_env, prod_version, dir)
            for f in os.listdir(zip_folder_path):
                if f.endswith('.zip'):
                    shutil.copy(os.path.join(zip_folder_path, f),
                                os.path.join(m_bytes_prod_web, f))
    print("All zips are now available in web folder")

    # Disconnect users from Production SDE to prohibit any schema locks if necessary
    arcpy.AcceptConnections(sde_prod_env, False)
    arcpy.DisconnectUser(sde_prod_env, "ALL")

    '''
    Export all necessary files from Bytes web directory to Production, Archive, and M: drive
    '''

    # Assign item list variable holding bytes files.
    bytes_dir_list = os.listdir(temp_env)

    # Loop through MapPLUTO Bytes Production directories for those that match current production version.

    for item in bytes_dir_list:
        if prod_version == item or prod_version.upper() == item:
            bytes_file_path = os.path.join(temp_env, item)

    # Assign item list variable holding versioned bytes files. --------------------------------------------

    bytes_file_list = os.listdir(bytes_file_path)

    # Assign path to Feature Classes in appropriate bytes directory. --------------------------------------

    for item in bytes_file_list:
        if item == "raw_data":
            bytes_features_path = os.path.join(bytes_file_path, item)
    print("Grabbing feature classes from the following path to push to Production SDE:")
    print(bytes_features_path)

    # Parse appropriate bytes directory and assign path for unclipped and clipped feature classes.

    arcpy.env.workspace = bytes_features_path
    bytes_gdbs = arcpy.ListWorkspaces()

    for item in bytes_gdbs:
        if "unclipped" in item:
            bytes_mp_unclipped_path = item
        else:
            bytes_mp_path = item

    # Print feature class names to confirm they are correct. -----------------------------------------------

    arcpy.env.workspace = bytes_mp_unclipped_path
    bytes_mp_unclipped_file = arcpy.ListFeatureClasses()[0]
    arcpy.env.workspace = bytes_mp_path
    bytes_mp_file = arcpy.ListFeatureClasses()[0]
    print("The following Feature Classes will be moved to Production SDE:")
    print(bytes_mp_file, bytes_mp_unclipped_file)

    # Rename previous production version to distinguish from incoming FCs. -----------------------------------

    arcpy.env.workspace = sde_prod_env

    print("Renaming Production's current version to append PREV_VERSION.")
    print("Renaming MapPLUTO to MapPLUTO_PREV_VERSION in SDE Production.")
    arcpy.Rename_management("MapPLUTO", "MapPLUTO_PREV_VERSION")
    print("Renaming complete.")
    print("Renaming MapPLUTO_UNCLIPPED to MapPLUTO_UNCLIPPED_PREV_VERSION in SDE Production.")
    arcpy.Rename_management("MapPLUTO_UNCLIPPED", "MapPLUTO_UNCLIPPED_PREV_VERSION")
    print("Renaming complete.")

    # Copy bytes FCs to production SDE with production naming convention. -----------------------------------

    print("Copying newest FCs from BytesProduction to SDE PROD.")
    print("Copying {0} as {1}".format(os.path.join(bytes_mp_path, bytes_mp_file),
                                      os.path.join(sde_prod_env, 'MapPLUTO')))
    arcpy.Copy_management(os.path.join(bytes_mp_path, bytes_mp_file),
                          os.path.join(sde_prod_env, 'MapPLUTO'))
    print("Copying {0} as {1}".format(os.path.join(bytes_mp_unclipped_path, bytes_mp_unclipped_file),
                                      os.path.join(sde_prod_env, 'MapPLUTO_UNCLIPPED')))
    arcpy.Copy_management(os.path.join(bytes_mp_unclipped_path, bytes_mp_unclipped_file),
                          os.path.join(sde_prod_env, 'MapPLUTO_UNCLIPPED'))
    print("Copying complete.")

    # Check archive SDE to make sure this version has not already been archived. --------------------------------
    # If it has not been archived, archive it with user input version number. -----------------------------------

    arcpy.env.workspace = sde_arch_env

    if arcpy.Exists(os.path.join(sde_arch_env, "MAPPLUTO_" + prod_version)):
        print("MapPLUTO {} clipped is already available in Archive SDE. Skipping archival of this dataset".format(prod_version))
    else:
        print("Copying {0} as {1}".format(os.path.join(sde_prod_env, 'MapPLUTO'),
                                          os.path.join(sde_arch_env, 'MapPLUTO_{}'.format(prod_version))))
        arcpy.Copy_management(os.path.join(sde_prod_env, 'MapPLUTO'),
                              os.path.join(sde_arch_env, 'MapPLUTO_{}'.format(prod_version)))

    if arcpy.Exists(os.path.join(sde_arch_env, "MAPPLUTO_" + prod_version + "_UNCLIPPED")):
        print("MapPLUTO {} unclipped is already available in Archive SDE. Skipping archival of this dataset".format(prod_version))
    else:
        print("Copying {0} as {1}".format(os.path.join(sde_prod_env, 'MapPLUTO_UNCLIPPED'),
                                          os.path.join(sde_arch_env,
                                                       'MapPLUTO_UNCLIPPED_{}'.format(prod_version))))
        arcpy.Copy_management(os.path.join(sde_prod_env, 'MapPLUTO_UNCLIPPED'),
                              os.path.join(sde_arch_env, 'MapPLUTO_UNCLIPPED_{}'.format(prod_version)))
    print("Copying complete.")

    # Delete MapPLUTO PREV VERSION from sde production since it has been archived in SDE Archive or already existed on SDE

    print("Connecting to production SDE workspace")
    arcpy.env.workspace = sde_prod_env
    print("Connection to production SDE complete.")

    arcpy.Delete_management('MapPLUTO_PREV_VERSION')
    arcpy.Delete_management('MapPLUTO_UNCLIPPED_PREV_VERSION')

    # Change workspace directory to production to pull source metadata and apply to production layer files.

    print("Connecting to production SDE workspace for metadata")
    arcpy.env.workspace = sde_prod_env
    print("Connection to production SDE complete.")

    all_boro_list = ["(Shoreline Clipped).lyr", "(Water Areas Included).lyr", "BBL only (Shoreline Clipped).lyr",
                     "BBL only (Water Areas Included).lyr", "Land Use (Shoreline Clipped).lyr",
                     "Land Use (Water Areas Included).lyr", "Land Use Plus (Shoreline Clipped).lyr",
                     "Land Use Plus (Water Areas Included).lyr"]

    arcpy.env.overwriteOutput = True

    # For each desired layer type, indicated in all_boro_list, create new xml files from Prod SDE source.

    for item in all_boro_list:
        if "Shoreline" in item:
            print("Exporting Clipped xml file to M:/GIS/DATA/MapPLUTO")
            arcpy.ExportMetadata_conversion("MapPLUTO", translator, os.path.join(m_path, "MapPLUTO " + item + ".xml"))
            print("Exporting Clipped xml file to M:/GIS/DATA/Building and Lots/MapPLUTO")
            arcpy.ExportMetadata_conversion("MapPLUTO", translator, os.path.join(m_bldg_path, "MapPLUTO" + item + ".xml"))

        elif "Water" in item:
            print("Exporting Unclipped xml file to M:/GIS/DATA/MapPLUTO")
            arcpy.ExportMetadata_conversion("MapPLUTO_UNCLIPPED", translator, os.path.join(m_path, "MapPLUTO " + item +
                                                                                           ".xml"))
            print("Exporting Unclipped xml file to M:/GIS/DATA/Building and Lots/MapPLUTO")
            arcpy.ExportMetadata_conversion("MapPLUTO_UNCLIPPED", translator, os.path.join(m_bldg_path, "MapPLUTO" + item +
                                                                                           ".xml"))

    # For each of the newly exported xml files, add the custom sentence describing the layer. ------------------------

    # Define function for updating metadata xml files with customized descriptive summary sentences

    def update_layer_xmls(directory_path, layer_name, custom_text):
        print("Modifying metadata for {}".format(layer_name))
        tree = ET.parse(os.path.join(directory_path, "MapPLUTO " + item + ".xml"))
        root = tree.getroot()
        for summary_text in root.iter("purpose"):
            print(summary_text.text)
            summary_text.text = summary_text.text + "\n\n" + custom_text
        tree.write(os.path.join(directory_path, "MapPLUTO " + item + ".xml"))

    for item in all_boro_list:
        # Update layers/xmls for M MapPLUTO path
        if item == "MapPLUTO (Shoreline Clipped).lyr":
            update_layer_xmls(m_path, "MapPLUTO Shoreline Clipped", "Shoreline clipped version does not contain lots " \
                                                    "completely or partially underwater.")

        elif item == "MapPLUTO (Water Included).lyr":
            update_layer_xmls(m_path, "MapPLUTO Water Included", "Layer: Water included version contains lots completely and " \
                                                    "partially underwater.")
        elif "BBL" in item and "Shoreline" in item:
            update_layer_xmls(m_path, "MapPLUTO BBL Only Shoreline Clipped", "Layer: BBL only version contains only the BBL field " \
                                                    "with no other attributes. Shoreline clipped version does not contain " \
                                                    "lots completely or partially underwater.")
        elif "BBL" in item and "Water" in item:
            update_layer_xmls(m_path, "MapPLUTO BBL Only Water Included", "Layer: Water included version contains lots completely " \
                                                    "and partially underwater.")
        elif "Plus" in item and "Shoreline" in item:
            update_layer_xmls(m_path, "MapPLUTO Land Use Plus Shoreline Clipped", "Layer: Land Use Plus version symbolizes data " \
                                                    "based on a combination of Land Use and Building Class categories " \
                                                    "(more granular than Land Use version). Shoreline clipped version " \
                                                    "does not contain lots completely or partially underwater.")
        elif "Plus" in item and "Water" in item:
            update_layer_xmls(m_path, "MapPLUTO Land Use Plus Water Included", "Layer: Land Use Plus version symbolizes data " \
                                                    "based on a combination of Land Use and Building Class categories " \
                                                    "(more granular than Land Use version). Water included version " \
                                                    "contains lots completely and partially underwater.")
        elif "Land Use (Shoreline Clipped)" in item:
            update_layer_xmls(m_path, "MapPLUTO Land Use Shoreline Clipped", "Layer: Land Use version symbolizes data based" \
                                                    "on DCP standard Land Use colors. Shoreline clipped version does " \
                                                    "not contain lots completely or partially underwater.")
        elif "Land Use (Water Included)" in item:
            update_layer_xmls(m_path, "MapPLUTO Land Use Water Included", "Layer: Land Use version symbolizes data based on " \
                                                    "DCP standard Land Use colors. Water included version contains " \
                                                    "lots completely and partially underwater.")

        # Update layers/xmls for M Bldg Lots MapPLUTO path

        if item == "MapPLUTO (Shoreline Clipped).lyr":
            update_layer_xmls(m_bldg_path, "MapPLUTO Shoreline Clipped", "Shoreline clipped version does not contain lots " \
                                                    "completely or partially underwater.")

        elif item == "MapPLUTO (Water Included).lyr":
            update_layer_xmls(m_bldg_path, "MapPLUTO Water Included", "Layer: Water included version contains lots completely and " \
                                                    "partially underwater.")
        elif "BBL" in item and "Shoreline" in item:
            update_layer_xmls(m_bldg_path, "MapPLUTO BBL Only Shoreline Clipped", "Layer: BBL only version contains only the BBL field " \
                                                    "with no other attributes. Shoreline clipped version does not contain " \
                                                    "lots completely or partially underwater.")
        elif "BBL" in item and "Water" in item:
            update_layer_xmls(m_bldg_path, "MapPLUTO BBL Only Water Included", "Layer: Water included version contains lots completely " \
                                                    "and partially underwater.")
        elif "Plus" in item and "Shoreline" in item:
            update_layer_xmls(m_bldg_path, "MapPLUTO Land Use Plus Shoreline Clipped", "Layer: Land Use Plus version symbolizes data " \
                                                    "based on a combination of Land Use and Building Class categories " \
                                                    "(more granular than Land Use version). Shoreline clipped version " \
                                                    "does not contain lots completely or partially underwater.")
        elif "Plus" in item and "Water" in item:
            update_layer_xmls(m_bldg_path, "MapPLUTO Land Use Plus Water Included", "Layer: Land Use Plus version symbolizes data " \
                                                    "based on a combination of Land Use and Building Class categories " \
                                                    "(more granular than Land Use version). Water included version " \
                                                    "contains lots completely and partially underwater.")
        elif "Land Use (Shoreline Clipped)" in item:
            update_layer_xmls(m_bldg_path, "MapPLUTO Land Use Shoreline Clipped", "Layer: Land Use version symbolizes data based" \
                                                    "on DCP standard Land Use colors. Shoreline clipped version does " \
                                                    "not contain lots completely or partially underwater.")
        elif "Land Use (Water Included)" in item:
            update_layer_xmls(m_bldg_path, "MapPLUTO Land Use Water Included", "Layer: Land Use version symbolizes data based on " \
                                                    "DCP standard Land Use colors. Water included version contains " \
                                                    "lots completely and partially underwater.")


    # Move README and Data Dictionary to M MapPLUTO path from BytesProduction --------------------------

    for item in os.listdir(os.path.join(temp_env, prod_version, "web")):
        if item.endswith("pdf") and item.startswith("PLUTO"):
            print("Copying {0} to {1}".format(os.path.join(temp_env, prod_version, "web", item),
                                              os.path.join(m_path, item)))
            shutil.copyfile(os.path.join(temp_env, prod_version, "web", item), os.path.join(m_path, item))
            print("Copying of file complete.")
        else:
            print("No available Data Dictionaries or User Guides to be pushed to M: drive MapPLUTO folders")

    arcpy.env.overwriteOutput = True

    # Generate xmls for borough -----------------------------------------------------------

    boroughs = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]
    borough_dict = {"Manhattan": "MN", "Bronx": "BX", "Brooklyn": "BK", "Queens": "QN", "Staten Island": "SI"}
    arcpy.env.workspace = sde_prod_env

    # Define function for assigning appropriate metadata information for various layer summaries

    def generate_layer_summaries(directory_path, input, summary_text):
        print('Generating xmls for {}'.format(lyr_item))
        arcpy.ExportMetadata_conversion(input, translator, os.path.join(directory_path, file_item, lyr_item + ".xml"))
        tree = ET.parse(os.path.join(directory_path, file_item, lyr_item + ".xml"))
        root = tree.getroot()
        for summary_item in root.iter("purpose"):
            summary_item.text = summary_item.text + "\n\n" + "Layer: {} Lots. {}".format(file_item, summary_text)
        tree.write(os.path.join(directory_path, file_item, lyr_item + ".xml"))

    # Define xml summary texts

    Default_Clipped_Summary = "Shoreline clipped version does not contain lots completely or partially underwater."
    Default_NonClipped_Summary = "Water included version contains lots completely and partially underwater."
    BBL_Clipped_Summary = "BBL only version contains only the BBL field with no other attributes. " \
                          "Shoreline clipped version does not contain lots completely or partially underwater"
    BBL_NonClipped_Summary = "BBL only version contains only the BBL field with no other attributes. " \
                             "Water included version contains lots completely and partially underwater."

    # Assign varying layer summary metadata information

    # Assigned for M MapPLUTO path
    for file_item in os.listdir(m_path):
        if file_item in boroughs:
            print("Generating xml files for {0} in {1}/{0}".format(file_item, m_path))
            borough_layers = [borough for borough in os.listdir(os.path.join(m_path, file_item)) if borough.endswith("lyr")]
            for lyr_item in borough_layers:
                if "BBL only" not in lyr_item and "Water" not in lyr_item:
                    generate_layer_summaries(m_path, "MapPLUTO", Default_Clipped_Summary)
                elif "BBL only" not in lyr_item and "Shoreline" not in lyr_item:
                    generate_layer_summaries(m_path, "MapPLUTO_UNCLIPPED", Default_NonClipped_Summary)
                elif "BBL only" in lyr_item and "Water" not in lyr_item:
                    generate_layer_summaries(m_path, "MapPLUTO", BBL_Clipped_Summary)
                elif "BBL only" in lyr_item and "Shoreline" not in lyr_item:
                    generate_layer_summaries(m_path, "MapPLUTO_UNCLIPPED", BBL_NonClipped_Summary)

    # Assigned for M Bldg and Lots MapPLUTO path

    for file_item in os.listdir(m_bldg_path):
        if file_item in boroughs:
            print("Generating xml files for {0} in {1}/{0}".format(file_item, m_bldg_path))
            borough_layers = [borough for borough in os.listdir(os.path.join(m_bldg_path, file_item)) if borough.endswith("lyr")]
            for lyr_item in borough_layers:
                if "BBL only" not in lyr_item and "Water" not in lyr_item:
                    generate_layer_summaries(m_bldg_path, "MapPLUTO", Default_Clipped_Summary)
                elif "BBL only" not in lyr_item and "Shoreline" not in lyr_item:
                    generate_layer_summaries(m_bldg_path, "MapPLUTO_UNCLIPPED", Default_NonClipped_Summary)
                elif "BBL only" in lyr_item and "Water" not in lyr_item:
                    generate_layer_summaries(m_bldg_path, "MapPLUTO", BBL_Clipped_Summary)
                elif "BBL only" in lyr_item and "Shoreline" not in lyr_item:
                    generate_layer_summaries(m_bldg_path, "MapPLUTO_UNCLIPPED", BBL_NonClipped_Summary)


    # Get MapPLUTO release date from previous xml export for Archive directory.

    tree = ET.parse(os.path.join(m_path, "MapPLUTO (Shoreline Clipped).lyr.xml"))
    root = tree.getroot()

    for pub_date in root.iter("pubdate"):
        print(pub_date.text[:11])
        release_date = pub_date.text[:11]

    release_date = datetime.datetime.strptime(release_date, "%Y%m%d")
    release_date_text = "(" + release_date.strftime("%b") + " " + str(release_date.year) + ")"

    # Archive Prod SDE as layers in M:GIS/DATA/Archive/MapPLUTO ----------------------------------------------------

    arcpy.env.workspace = sde_prod_env

    layer_symb_path = config.get('PATHS', 'Layer_Symbology_Path')

    # Define function for creating necessary new layers in the Archive directory

    def layer_meta_archive(input, clip_val, clip_text):
        print("Archiving MapPLUTO {}".format(clip_text))
        print("Creating in-memory layer.")
        arcpy.MakeFeatureLayer_management(input, input + prod_version + clip_val)
        print("Saving layer to appropriate path.")
        arcpy.SaveToLayerFile_management(input + prod_version + clip_val, os.path.join(m_arch_path,
                                                                                       input.replace("_UNLCIPPED", "")  + " " + prod_version + " " +
                                                                                       release_date_text + " - {}".format(clip_text)))
        print("Exporting metadata xmls to appropriate path")
        arcpy.ExportMetadata_conversion(input, translator, os.path.join(m_arch_path,
                                                                        input.replace("_UNLCIPPED", "") + " " + prod_version + " " + release_date_text
                                                                         + " - {}.lyr.xml".format(clip_text)))
        print("Applying appropriate symbology from previous export")
        arcpy.ApplySymbologyFromLayer_management(os.path.join(m_arch_path,
                                                              input.replace("_UNLCIPPED", "") + " " + prod_version + " " + release_date_text
                                                              + " - {}.lyr".format(clip_text)), layer_symb_path)

    layer_meta_archive("MapPLUTO", "Shoreline", "Shoreline Clipped")
    layer_meta_archive("MapPLUTO_UNCLIPPED", "Water", "Water Included")

    '''
    Below section was previously used for exporting CARTO version of MapPLUTO for Labs / DE. This step has been replaced with
    a stand-alone script. Leaving commented for now and can remove in the future if no longer desired. - AF 
    '''

    # # Export CARTO version shapefiles to Bytes Production -----------------------------------------------------------
    #
    # m_bytes_prod_carto = os.path.join(m_bytes_version_path, 'carto')
    #
    # if os.path.isdir(m_bytes_prod_carto):
    #     print("CARTO directory in BytesProduction already exists. Skipping directory generation step.")
    # else:
    #     os.mkdir(m_bytes_prod_carto)
    #
    # for f in os.listdir(m_bytes_prod_shape):
    #     # Copying MapPLUTO Clipped to CARTO Directory
    #     if "MapPLUTO" in f and "_" not in f and ".zip" not in f:
    #         print("Copying {} to {}".format(os.path.join(m_bytes_prod_shape, f), os.path.join(m_bytes_prod_carto, f)))
    #         shutil.copyfile(os.path.join(m_bytes_prod_shape, f),
    #                              os.path.join(m_bytes_prod_carto, f[:8] + "_{}".format(prod_version) + f[8:]))
    #         print("{} copied.".format(f))
    #
    # for f in os.listdir(m_bytes_prod_carto):
    #     if '.shp' in f and 'xml' not in f:
    #         print("Adding spatial index to CARTO version of MapPLUTO data set.")
    #         arcpy.AddSpatialIndex_management(os.path.join(m_bytes_prod_carto, f))
    #         print("Spatial index added to CARTO version of MapPLUTO data set.")
    #         print("Repairing geometry of CARTO version of MapPLUTO data set.")
    #         arcpy.RepairGeometry_management(os.path.join(m_bytes_prod_carto, f))
    #         print("Geometry repaired for CARTO version of MapPLUTO data set.")
    #
    # carto_zip = zipfile.ZipFile(os.path.join(m_bytes_prod_carto, 'MapPLUTO_{}.zip'.format(prod_version)), 'w')
    #
    # for f in os.listdir(m_bytes_prod_carto):
    #     if ".zip" not in f:
    #         print("Zipping {}".format(os.path.join(m_bytes_prod_carto, f)))
    #         carto_zip.write(os.path.join(m_bytes_prod_carto, f), f, compress_type=zipfile.ZIP_DEFLATED)
    #         print("{} added to zip directory.".format(os.path.join(m_bytes_prod_carto, f)))
    # carto_zip.close()

    '''
    Rename exports to match naming convention for layers. Typically not used.
    Only necessary for beta versioning. E.g. 18v1.1 or 19v2.3, etc. Anything with .
    Not necessary for non-beta versioning. E.g. 18v2 or 18v1 or 19v1, etc.
    
    print("Renaming exported layers to replace _ with . within version number.")
    for item in os.listdir(m_arch_path):
        if prod_version in item:
            os.rename(os.path.join(m_arch_path, item), os.path.join(m_arch_path, item.replace("_", ".")))
    '''

    EndTime = datetime.datetime.now().replace(microsecond = 0)
    print("Script runtime: {}".format(EndTime - StartTime))
    log.write(str(StartTime) + "\t" + str(EndTime) + "\t" + str(EndTime - StartTime) + "\n")
    log.close()

    arcpy.AcceptConnections(sde_prod_env, True)

except:
    arcpy.AcceptConnections(sde_prod_env, True)
    print "error"
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages() + "\n"

    print pymsg
    print msgs

    log.write("" + pymsg + "\n")
    log.write("" + msgs + "")
    log.write("\n")
    log.close()