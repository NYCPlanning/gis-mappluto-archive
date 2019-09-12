# Must be run with ArcPy Python27 32-bit version

import os, re, xml.etree.ElementTree as ET, arcpy, shutil, zipfile, datetime, sys, traceback, ConfigParser


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
    m_path = config.get('PATHS', 'M_Path')
    m_arch_path = config.get('PATHS', 'M_Archive_Path')
    x_path = config.get('PATHS', 'X_Path')
    today_dt = datetime.datetime.now()
    today = today_dt.strftime('%m_%d_%Y')
    prod_version = '18v2_1'
    prev_prod_version = '18v2'

    # Check Bytes directory for version dir -------------------------------------------------------------

    bytes_dirs = ['csv', 'fgdb', 'meta', 'Raw_data', 'shapefiles', 'web']

    dir_list = []

    for item in os.listdir(bytes_env):
        dir_list.append(item)
        print(dir_list)

    m_bytes_version_path = os.path.join(bytes_env, prod_version)

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

    # Check MapPLUTO output location for fgdbs/shapefiles/original/etc -----------------------------------

    print("Parsing MapPLUTOCSV2FC output folder for appropriate version directory on X: drive")
    output_list = os.listdir(x_path)

    if prod_version in output_list:
        x_src_path = os.path.join(x_path, prod_version)
        x_output_path = os.path.join(x_path, prod_version, 'outputs')
    else:
        print("No outputs for {} currently available. Aborting script".format(prod_version))
        sys.exit()

    # Export csv and zipped csv to Bytes Production -----------------------------------------------------

    if os.path.exists(x_src_path):
        src_dir_list = os.listdir(x_src_path)
        m_bytes_prod_csv = os.path.join(bytes_env, prod_version, 'csv')
        for item in src_dir_list:
            if 'pluto' in item and item.endswith('.csv'):
                if os.path.exists(os.path.join(m_bytes_prod_csv, 'pluto_{}.csv'.format(prod_version))):
                    print("Original PLUTO csv already exists in Bytes/{}/csv.".format(prod_version))
                else:
                    print("Original PLUTO csv does not exist in Bytes/{}/csv. Copying now.".format(prod_version))
                    shutil.copyfile(os.path.join(x_src_path, item),
                                    os.path.join(m_bytes_prod_csv,
                                                 'pluto_{}.csv'.format(prod_version)))
                    print("Copy of PLUTO csv complete.")
                if os.path.exists(os.path.join(m_bytes_prod_csv, 'nyc_pluto_{}_csv.zip'.format(prod_version))):
                    print("Zip of original PLUTO csv already exists in Bytes/{}/csv".format(prod_version))
                else:
                    print("Zip of original PLUTO csv does not exist in Bytes/{}/csv. Copying now.".format(prod_version))
                    mp_src_zip = zipfile.ZipFile(os.path.join(m_bytes_prod_csv,
                                                              'nyc_pluto_{}_csv.zip'.format(prod_version)), 'w')
                    mp_src_zip.write(os.path.join(m_bytes_prod_csv, 'pluto_{}.csv'.format(prod_version)),
                                     compress_type=zipfile.ZIP_DEFLATED)
                    mp_src_zip.close()

    # Export metadata to BytesProduction directory using old MapPLUTO Production source and modifying certain desired
    # xml fields.

    Arcdir = arcpy.GetInstallInfo("desktop")["InstallDir"]
    translator = Arcdir + "Metadata/Translator/ARCGIS2FGDC.xml"

    sde_prod_clip_meta = config.get('PATHS', 'MapPLUTO_SDE_Clipped_Path')
    sde_prod_unclip_meta = config.get('PATHS', 'MapPLUTO_SDE_Unclipped_Path')
    m_bytes_prod_meta = os.path.join(bytes_env, prod_version, 'meta')

    if os.path.exists(os.path.join(m_bytes_prod_meta, 'PLUTOmeta.xml')):
        print("PLUTO meta already exists in BytesProduction. Skipping")
    else:
        print("Exporting MapPLUTO clipped metadata files to BytesProduction meta folders")
        arcpy.ExportMetadata_conversion(sde_prod_clip_meta,
                                        translator,
                                        os.path.join(m_bytes_prod_meta, 'PLUTOmeta.xml'))

    def replace_xml_content(input):
        tree = ET.parse(os.path.join(m_bytes_prod_meta), input)
        root = tree.getroot()
        for item in root.iter("pubdate"):
            item.text = str(today)
        for item in root.iter("edition"):
            item.text = str(prod_version)
        for item in root.iter("issue"):
            item.text = "MapPLUTO {}".format(prod_version)
        for item in root.iter("title"):
            item.text = "New York City, MapPLUTO {}".format(prod_version)
        for item in root.getiterator():
            try:
                item.text = item.text.replace(prev_prod_version, prod_version)
            except AttributeError:
                pass
        tree.write(os.path.join(m_bytes_prod_meta, input))

    if os.path.exists(os.path.join(m_bytes_prod_meta)):
        replace_xml_content("PLUTOmeta.xml")

    if os.path.exists(os.path.join(m_bytes_prod_meta, 'PLUTOmeta_unclip.xml')):
        print("PLUTO unclipped meta already exists in BytesProduction. Skipping")
    else:
        print("Exporting MapPLUTO unclipped metadata files to BytesProduction meta folders")
        replace_xml_content("PLUTOmeta_unclip.xml")

    # Export standard shapefiles to Bytes Production -----------------------------------

    arcpy.env.workspace = x_output_path
    output_gdb_list = arcpy.ListWorkspaces('*', 'FileGDB')
    m_bytes_prod_shape = os.path.join(bytes_env, prod_version, 'shapefiles')

    if os.path.exists(os.path.join(x_output_path, 'MapPLUTO_{}.gdb'.format(prod_version))) \
            and os.path.exists(os.path.join(x_output_path, 'MapPLUTO_{}_unclipped.gdb'.format(prod_version))):
        if os.path.exists(os.path.join(m_bytes_prod_shape, 'MAPPLUTO.SHP')) \
                and os.path.exists(os.path.join(m_bytes_prod_shape, 'MAPPLUTO_UNCLIPPED.SHP')):
            print("MapPLUTO Shapefile exports already exist in BytesProduction directory")
        else:
            for fgdb in output_gdb_list:
                gdb_env = os.path.join(x_output_path, fgdb)
                arcpy.env.workspace = gdb_env
                fgdb_avail = arcpy.ListFeatureClasses()
                for item in fgdb_avail:
                    if 'MapPLUTO' in item:
                        print("Exporting MapPLUTO shapefiles to BytesProduction shapefile directory.")
                        arcpy.FeatureClassToShapefile_conversion(os.path.join(x_output_path, fgdb, item),
                                                                 os.path.join(m_bytes_prod_shape))
                    else:
                        print("The following is not an adequate shapefile for upload")

    # Export zipped shapefiles to Bytes Production -----------------------------------

    shoreline_zip = zipfile.ZipFile(os.path.join(m_bytes_prod_shape,
                                                         'nyc_mappluto_{}_shp.zip'.format(prod_version)), mode='w')
    water_area_zip = zipfile.ZipFile(os.path.join(m_bytes_prod_shape,
                                                  'nyc_mappluto_{}_unclipped_shp.zip'.format(prod_version)), mode='w')

    # Define function for zipping requisite shapefile files --------------------------

    def zip_shapefiles(filename, zip_path):
        for f in os.listdir(os.path.join(m_bytes_prod_shape)):
            if "MapPLUTO_UNCLIPPED" not in f and not f.endswith(".xml"):
                if f.endswith(".shp") or f.endswith(".SHP"):
                    arcpy.ImportMetadata_conversion(os.path.join(m_bytes_prod_meta, "PLUTOmeta.xml"),
                                                    "FROM_FGDC",
                                                    os.path.join(m_bytes_prod_shape,
                                                                 f.replace("_{}_{}".format(today, filename), "").upper()))
        for f in os.listdir(os.path.join(m_bytes_prod_shape)):
            if "MapPLUTO_UNCLIPPED" not in f:
                if f.endswith(".xml") or f.endswith(".XML") or f.endswith(".lock"):
                    print("Deleting {}".format(f))
                    arcpy.Delete_management(f)
                if f.endswith(("cpg", "dbf", "prj", "sbn", "sbx", "shp")):
                    zip_path.write(os.path.join(m_bytes_prod_shape, f), f, compress_type=zipfile.ZIP_DEFLATED)
        zip_path.close()

    zip_shapefiles("Shoreline_ClippedProj", shoreline_zip)
    zip_shapefiles("Water_IncludedProj", water_area_zip)

    print("Shapefile export complete")

    # Export fgdbs and zipped fgdbs to Bytes Production -----------------------------------

    m_bytes_prod_fgdb = os.path.join(bytes_env, prod_version, 'fgdb')

    if os.path.join(x_output_path, 'MapPLUTO_WaterArea_{}.gdb'.format(today)) and \
            os.path.join(x_output_path, 'MapPLUTO_ShorelineClip_{}.gdb'.format(today)) in output_gdb_list:
        print("Exporting MapPLUTO GDBs to BytesProduction fgdb directory.")
        for gdb in output_gdb_list:
            if 'Water' in gdb:

                # Export MapPLUTO Unclipped FGDB ---------------------------------------------------------

                if os.path.exists(os.path.join(m_bytes_prod_fgdb,
                                               'MapPLUTO_{}_unclipped.gdb'.format(prod_version))):
                    print("MapPLUTO Unclipped fgdb already exported.")
                else:
                    print("MapPLUTO Unclipped is being copied to Bytes Production fgdb directory")
                    shutil.copytree(os.path.join(x_output_path, gdb), os.path.join(m_bytes_prod_fgdb,
                                                                           'MapPLUTO_{}_unclipped.gdb'.format(prod_version)))
                    arcpy.ImportMetadata_conversion(os.path.join(m_bytes_prod_meta, 'PLUTOmeta_unclip.xml'),
                                                    'FROM_FGDC', os.path.join(m_bytes_prod_fgdb,
                                                                              'MapPLUTO_{}_unclipped.gdb'.format(prod_version),
                                                                              'MapPLUTO_UNCLIPPED'.format(today)))

                # Export MapPLUTO Unclipped FGDB zips ------------------------------------------------------

                if os.path.exists(os.path.join(m_bytes_prod_fgdb,
                                               'nyc_mappluto_{}_unclipped_fgdb.zip'.format(prod_version))):
                    print("MapPLUTO Unclipped fgdb zip already exported.")
                else:
                    mp_unclipped_zip = zipfile.ZipFile(os.path.join(m_bytes_prod_fgdb,
                                                                'nyc_mappluto_{}_unclipped_fgdb.zip'.format(prod_version)), mode='w')
                    try:
                        print("Zipping MapPLUTO Unclipped for Bytes Production fgdb directory")
                        for f in os.listdir(os.path.join(x_output_path, gdb)):
                            mp_unclipped_zip.write(os.path.join(x_output_path, gdb, f),
                                                   "MapPLUTO_{}_unclipped.gdb\\".format(prod_version) + f,
                                                   compress_type=zipfile.ZIP_DEFLATED)
                    finally:
                        print("Zip of MapPLUTO Unclipped complete.")
                        mp_unclipped_zip.close()

                print("MapPLUTO Unclipped copy complete.")
            else:
                # Export MapPLUTO Clipped FGDB --------------------------------------------------------------

                if os.path.exists(os.path.join(m_bytes_prod_fgdb,
                                               'MapPLUTO_{}.gdb'.format(prod_version))):
                    print("MapPLUTO clipped fgdb already exported")
                else:
                    print("MapPLUTO clipped is being copied to Bytes Production fgdb")
                    arcpy.Copy_management(os.path.join(x_output_path, gdb), os.path.join(m_bytes_prod_fgdb,
                                                                           'MapPLUTO_{}.gdb'.format(prod_version)))
                    arcpy.ImportMetadata_conversion(
                        os.path.join(bytes_env, prod_version, 'meta', 'PLUTOmeta.xml'),
                        'FROM_FGDC', os.path.join(m_bytes_prod_fgdb,
                                                  'MapPLUTO_{}.gdb'.format(prod_version),
                                                  'MapPLUTO'.format(today)))

                # Export MapPLUTO Clipped FGDB zips ---------------------------------------------------------

                if os.path.exists(os.path.join(m_bytes_prod_fgdb,
                                               'nyc_mappluto_{}_fgdb.zip')):
                    print("MapPLUTO clipped fgdb zip already exported")
                else:
                    mp_clipped_zip = zipfile.ZipFile(os.path.join(m_bytes_prod_fgdb,
                                                              'nyc_mappluto_{}_fgdb.zip'.format(prod_version)), mode='w')
                    try:
                        print("Zipping MapPLUTO Clipped for Bytes Production fgdb directory")
                        for f in os.listdir(os.path.join(x_output_path, gdb)):
                            mp_clipped_zip.write(os.path.join(x_output_path, gdb, f),
                                                 "MapPLUTO_{}.gdb\\".format(prod_version) + f,
                                                 compress_type= zipfile.ZIP_DEFLATED)
                    finally:
                        print("Zip of MapPLUTO Clipped complete.")
                        mp_clipped_zip.close()

                print("MapPLUTO clipped copy complete.")
    else:
        print("The MapPLUTO output directory on the X: drive is lacking one or both of the required GDBs")

    # Export zips to Bytes Production web directory

    for item in os.listdir(m_bytes_version_path):
        if item.endswith('') and 'web' not in item:
            sub_dir_path = os.path.join(m_bytes_version_path, item)
            for item2 in os.listdir(sub_dir_path):
                if item2.endswith('.zip'):
                    shutil.copy2(os.path.join(sub_dir_path, item2), os.path.join(bytes_env, prod_version, 'web'))
        if item.endswith('.zip'):
            shutil.copy2(os.path.join(bytes_env, item), os.path.join(bytes_env, prod_version, 'web'))

    '''
    Export all necessary files from Bytes web directory to Production, Archive, and M: drive
    '''

    # Assign item list variable holding bytes files.
    bytes_dir_list = os.listdir(bytes_env)

    # Loop through MapPLUTO Bytes Production directories for those that match current production version.

    for item in bytes_dir_list:
        if prod_version == item or prod_version.upper() == item:
            bytes_file_path = os.path.join(bytes_env, item)

    # Assign item list variable holding versioned bytes files. --------------------------------------------

    bytes_file_list = os.listdir(bytes_file_path)

    # Assign path to Feature Classes in appropriate bytes directory. --------------------------------------

    for item in bytes_file_list:
        if item == "fgdb":
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
                                      os.path.join(sde_prod_env, bytes_mp_file)))
    arcpy.Copy_management(os.path.join(bytes_mp_path, bytes_mp_file),
                          os.path.join(sde_prod_env, bytes_mp_file))
    print("Copying {0} as {1}".format(os.path.join(bytes_mp_unclipped_path, bytes_mp_unclipped_file),
                                      os.path.join(sde_prod_env, bytes_mp_unclipped_file)))
    arcpy.Copy_management(os.path.join(bytes_mp_unclipped_path, bytes_mp_unclipped_file),
                          os.path.join(sde_prod_env, bytes_mp_unclipped_file))
    print("Copying complete.")

    # Check archive SDE to make sure this version has not already been archived. --------------------------------
    # If it has not been archived, archive it with user input version number. -----------------------------------

    arcpy.env.workspace = sde_arch_env

    if arcpy.Exists(os.path.join(sde_arch_env, "MAPPLUTO_" + prod_version)) or arcpy.Exists(os.path.join(sde_arch_env, "MAPPLUTO_" + prod_version + "_UNCLIPPED")):
        print("The desired version already exists in Archive SDE. Skipping this step")
    else:
        print("Copying version {} to Archive SDE".format(prod_version))
        print("Copying {0} as {1}".format(os.path.join(bytes_mp_path, bytes_mp_file),
                                          os.path.join(sde_arch_env, bytes_mp_file.upper() + "_" + prod_version)))
        arcpy.Copy_management(os.path.join(bytes_mp_path, bytes_mp_file),
                              os.path.join(sde_arch_env, bytes_mp_file.upper() + "_" + prod_version))
        print("Copying {0} as {1}".format(os.path.join(bytes_mp_unclipped_path, bytes_mp_unclipped_file),
                                          os.path.join(sde_arch_env,
                                                       bytes_mp_unclipped_file.upper().replace("UNCLIPPED",
                                                                                               prod_version +
                                                                                               "_UNCLIPPED"))))
        arcpy.Copy_management(os.path.join(bytes_mp_unclipped_path, bytes_mp_unclipped_file),
                              os.path.join(sde_arch_env,
                                           bytes_mp_unclipped_file.upper().replace("UNCLIPPED",
                                                                                   prod_version + "_UNCLIPPED")))
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

    all_boro_list = ["(Shoreline Clipped).lyr", "(Water Included).lyr", "BBL only (Shoreline Clipped).lyr",
                     "BBL only (Water Included).lyr", "Land Use (Shoreline Clipped).lyr", "Land Use (Water Included).lyr",
                     "Land Use Plus (Shoreline Clipped).lyr", "Land Use Plus (Water Included).lyr"]

    arcpy.env.overwriteOutput = True

    # For each desired layer type, indicated in all_boro_list, create new xml files from Prod SDE source.

    for item in all_boro_list:
        if "Shoreline" in item:
            print("Exporting Clipped xml file to M:/GIS/DATA/MapPLUTO")
            arcpy.ExportMetadata_conversion("MapPLUTO", translator, os.path.join(m_path, "MapPLUTO-" + item + ".xml"))

        elif "Water" in item:
            print("Exporting Unclipped xml file to M:/GIS/DATA/MapPLUTO")
            arcpy.ExportMetadata_conversion("MapPLUTO_UNCLIPPED", translator, os.path.join(m_path, "MapPLUTO-" + item +
                                                                                           ".xml"))

    # For each of the newly exported xml files, add the custom sentence describing the layer. ------------------------

    # Define function for updating metadata xml files with customized descriptive summary sentences

    def update_layer_xmls(layer_name, custom_text):
        print("Modifying metadata for {}".format(layer_name))
        tree = ET.parse(os.path.join(m_path, "MapPLUTO-" + item + ".xml"))
        root = tree.getroot()
        for summary_text in root.iter("purpose"):
            print(summary_text.text)
            summary_text.text = summary_text.text + "\n\n" + custom_text
        tree.write(os.path.join(m_path, "MapPLUTO-" + item + ".xml"))

    for item in all_boro_list:
        if item == "MapPLUTO-(Shoreline Clipped).lyr":
            update_layer_xmls("MapPLUTO Shoreline Clipped", "Shoreline clipped version does not contain lots " \
                                                    "completely or partially underwater.")

        elif item == "MapPLUTO-(Water Included).lyr":
            update_layer_xmls("MapPLUTO Water Included", "Layer: Water included version contains lots completely and " \
                                                    "partially underwater.")
        elif "BBL" in item and "Shoreline" in item:
            update_layer_xmls("MapPLUTO BBL Only Shoreline Clipped", "Layer: BBL only version contains only the BBL field " \
                                                    "with no other attributes. Shoreline clipped version does not contain " \
                                                    "lots completely or partially underwater.")
        elif "BBL" in item and "Water" in item:
            update_layer_xmls("MapPLUTO BBL Only Water Included", "Layer: Water included version contains lots completely " \
                                                    "and partially underwater.")
        elif "Plus" in item and "Shoreline" in item:
            update_layer_xmls("MapPLUTO Land Use Plus Shoreline Clipped", "Layer: Land Use Plus version symbolizes data " \
                                                    "based on a combination of Land Use and Building Class categories " \
                                                    "(more granular than Land Use version). Shoreline clipped version " \
                                                    "does not contain lots completely or partially underwater.")
        elif "Plus" in item and "Water" in item:
            update_layer_xmls("MapPLUTO Land Use Plus Water Included", "Layer: Land Use Plus version symbolizes data " \
                                                    "based on a combination of Land Use and Building Class categories " \
                                                    "(more granular than Land Use version). Water included version " \
                                                    "contains lots completely and partially underwater.")
        elif "Land Use (Shoreline Clipped)" in item:
            update_layer_xmls("MapPLUTO Land Use Shoreline Clipped", "Layer: Land Use version symbolizes data based" \
                                                    "on DCP standard Land Use colors. Shoreline clipped version does " \
                                                    "not contain lots completely or partially underwater.")
        elif "Land Use (Water Included)" in item:
            update_layer_xmls("MapPLUTO Land Use Water Included", "Layer: Land Use version symbolizes data based on " \
                                                    "DCP standard Land Use colors. Water included version contains " \
                                                    "lots completely and partially underwater.")

    # Move README and Data Dictionary to M:/GIS/DATA/MAPPLUTO from BytesProduction --------------------------

    for item in os.listdir(os.path.join(bytes_env, prod_version, "web")):
        if item.endswith("pdf") and item.startswith("PLUTO"):
            print("Copying {0} to {1}".format(os.path.join(bytes_env, prod_version, "web", item),
                                              os.path.join(m_path, item)))
            shutil.copyfile(os.path.join(bytes_env, prod_version, "web", item), os.path.join(m_path, item))
            print("Copying of file complete.")
        else:
            print("No available Data Dictionaries or User Guides to be pushed to M: drive MapPLUTO folders")

    arcpy.env.overwriteOutput = True

    # Generate xmls for borough -----------------------------------------------------------

    boroughs = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]
    borough_dict = {"Manhattan": "MN", "Bronx": "BX", "Brooklyn": "BK", "Queens": "QN", "Staten Island": "SI"}
    arcpy.env.workspace = sde_prod_env

    # Define function for assigning appropriate metadata information for various layer summaries

    def generate_layer_summaries(input, summary_text):
        print('Generating xmls for {}'.format(lyr_item))
        arcpy.ExportMetadata_conversion(input, translator, os.path.join(m_path, file_item, lyr_item + ".xml"))
        tree = ET.parse(os.path.join(m_path, file_item, lyr_item + ".xml"))
        root = tree.getroot()
        for summary_item in root.iter("purpose"):
            summary_item.text = summary_item.text + "\n\n" + "Layer: {} Lots. {}".format(file_item, summary_text)
        tree.write(os.path.join(m_path, file_item, lyr_item + ".xml"))

    # Define xml summary texts

    Default_Clipped_Summary = "Shoreline clipped version does not contain lots completely or partially underwater."
    Default_NonClipped_Summary = "Water included version contains lots completely and partially underwater."
    BBL_Clipped_Summary = "BBL only version contains only the BBL field with no other attributes. " \
                          "Shoreline clipped version does not contain lots completely or partially underwater"
    BBL_NonClipped_Summary = "BBL only version contains only the BBL field with no other attributes. " \
                             "Water included version contains lots completely and partially underwater."

    # Assign varying layer summary metadata information

    for file_item in os.listdir(m_path):
        if file_item in boroughs:
            print("Generating xml files for {0} in {1}/{0}".format(file_item, m_path))
            borough_layers = [borough for borough in os.listdir(os.path.join(m_path, file_item)) if borough.endswith("lyr")]
            for lyr_item in borough_layers:
                if "BBL only" not in lyr_item and "Water" not in lyr_item:
                    generate_layer_summaries("MapPLUTO", Default_Clipped_Summary)
                elif "BBL only" not in lyr_item and "Shoreline" not in lyr_item:
                    generate_layer_summaries("MapPLUTO_UNCLIPPED", Default_NonClipped_Summary)
                elif "BBL only" in lyr_item and "Water" not in lyr_item:
                    generate_layer_summaries("MapPLUTO", BBL_Clipped_Summary)
                elif "BBL only" in lyr_item and "Shoreline" not in lyr_item:
                    generate_layer_summaries("MapPLUTO_UNCLIPPED", BBL_NonClipped_Summary)

    # Get MapPLUTO release date from previous xml export for Archive directory.

    tree = ET.parse(os.path.join(m_path, "MapPLUTO-(Shoreline Clipped).lyr.xml"))
    root = tree.getroot()

    for pub_date in root.iter("pubdate"):
        print(pub_date.text[:11])
        release_date = pub_date.text[:11]

    release_date = datetime.strptime(release_date, "%Y%m%d")
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
                                                                                       input + prod_version + " " +
                                                                                       release_date_text + " - {}".format(clip_text)))
        print("Exporting metadata xmls to appropriate path")
        arcpy.ExportMetadata_conversion(input, translator, os.path.join(m_arch_path,
                                                                        input + prod_version + " " + release_date_text
                                                                         + " - {}.lyr.xml".format(clip_text)))
        print("Applying appropriate symbology from previous export")
        arcpy.ApplySymbologyFromLayer_management(os.path.join(m_arch_path,
                                                              input + prod_version + " " + release_date_text
                                                              + " - {}.lyr".format(clip_text), layer_symb_path))

    layer_meta_archive("MapPLUTO", "Shoreline", "Shoreline Clipped")
    layer_meta_archive("MapPLUTO_UNCLIPPED", "Water", "Water Included")

    # Export CARTO version shapefiles to Bytes Production -----------------------------------------------------------

    m_bytes_prod_carto = os.path.join(m_bytes_version_path, 'carto')

    if os.path.isdir(m_bytes_prod_carto):
        print("CARTO directory in BytesProduction already exists. Skipping directory generation step.")
    else:
        os.mkdir(m_bytes_prod_carto)

    for f in os.listdir(m_bytes_prod_shape):
        # Copying MapPLUTO Clipped to CARTO Directory
        if "MapPLUTO" in f and "_" not in f and ".zip" not in f:
            print("Copying {} to {}".format(os.path.join(m_bytes_prod_shape, f), os.path.join(m_bytes_prod_carto, f)))
            shutil.copyfile(os.path.join(m_bytes_prod_shape, f),
                                 os.path.join(m_bytes_prod_carto, f[:8] + "_{}".format(prod_version) + f[8:]))
            print("{} copied.".format(f))

    for f in os.listdir(m_bytes_prod_carto):
        if '.shp' in f and 'xml' not in f:
            print("Adding spatial index to CARTO version of MapPLUTO data set.")
            arcpy.AddSpatialIndex_management(os.path.join(m_bytes_prod_carto, f))
            print("Spatial index added to CARTO version of MapPLUTO data set.")
            print("Repairing geometry of CARTO version of MapPLUTO data set.")
            arcpy.RepairGeometry_management(os.path.join(m_bytes_prod_carto, f))
            print("Geometry repaired for CARTO version of MapPLUTO data set.")

    carto_zip = zipfile.ZipFile(os.path.join(m_bytes_prod_carto, 'MapPLUTO_{}.zip'.format(prod_version)), 'w')

    for f in os.listdir(m_bytes_prod_carto):
        if ".zip" not in f:
            print("Zipping {}".format(os.path.join(m_bytes_prod_carto, f)))
            carto_zip.write(os.path.join(m_bytes_prod_carto, f), f, compress_type=zipfile.ZIP_DEFLATED)
            print("{} added to zip directory.".format(os.path.join(m_bytes_prod_carto, f)))
    carto_zip.close()

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

except:
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