import os
import subprocess
import requests
import datetime
from dateutil.relativedelta import relativedelta

# Fill in the following configuration parameters
osm_history_file_path = r"data/history-latest.osm.pbf"
city_polys_output_directory = r"data/outputs/citypolys"
city_pbfs_output_directory = r"data/outputs/citypbfs"
city_relation_osm_ids = [2062154,7486330] # waterloo, stratford
#city_relation_osm_ids = [7433781, 7433486] # leamington, kingsville
#city_relation_osm_ids = [7433781]
start_date = datetime.datetime(2010,1,1,0,0,0)
end_date = datetime.datetime.now()

def get_city_poly_file(id):
    """Given a relation ID, get the associated .poly file"""
    print("Attempting to get .poly file for relation {}...".format(str(id)))
    r = requests.get("http://polygons.openstreetmap.fr/get_poly.py?id={}&params=0".format(str(id)))
    print("Request returned with code {}".format(r.status_code))
    if r.status_code == 200:
        city_output_poly_file = str(id) + ".poly"
        city_output_poly_path = city_polys_output_directory + os.sep + city_output_poly_file
        file = open(city_output_poly_path,"w")
        file.write (r.text)
        file.close()
        return city_output_poly_path
    else:
        raise Exception(r.status_code) 

def extract_city_from_history(id, city_output_poly_path):
    # Extract the features from the full history file that are within the city polygon
    # This will take a while (1-2 hours)
    city_output_pbf_file = city_pbfs_output_directory + os.sep + str(id) + ".osm.pbf"
    print("Extracting city {}...".format(str(id)))
    result = subprocess.run(["osmium", 
                    "extract",
                    "--overwrite", 
                    "-p", 
                    city_output_poly_path, 
                    "--with-history", 
                    osm_history_file_path, 
                    "-o", 
                    city_output_pbf_file])
    if result.returncode == 0:
        print("Completed extracting city {} to {}".format(str(id),city_output_pbf_file))
        return city_output_pbf_file
    else:
        # raises an exception if return code is non-zero
        result.check_returncode()

def snapshot_city_at_timestamp(city_output_pbf_file, timestamp, id):
    timestamp_s = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    year_month = timestamp.strftime("%Y_%m")
    timed_city_output_pbf = city_pbfs_output_directory + os.sep + str(id) + "." + year_month + ".osm.pbf"
    print("Filtering for {}".format(timestamp))
    result = subprocess.run(["osmium",
                    "time-filter",
                    city_output_pbf_file,
                    timestamp_s,
                    "--overwrite",
                    "-o",
                    timed_city_output_pbf])
    if result.returncode == 0:
        print("Completed temporal filter: {}".format(timed_city_output_pbf))
        return timed_city_output_pbf
    else:
        result.check_returncode()

def extract_buildings_from_snapshot(timed_city_output_pbf, id):
    buildings_pbf = city_pbfs_output_directory + os.sep + str(id) + "." + year_month + ".buildings" + ".osm.pbf"
    print("Filtering {} for buildings".format(timed_city_output_pbf))
    result = subprocess.run(["osmium",
                            "tags-filter",
                            timed_city_output_pbf,
                            "building",
                            "--overwrite",
                            "-o",
                            buildings_pbf])
    if result.returncode == 0:
        print("Buildings filtered to {}".format(buildings_pbf))
        return buildings_pbf
    else:
        result.check_returncode()

def import_buildings_into_db(buildings_pbf, id):
    print("Importing into database...")
    result = subprocess.run(["osm2pgsql",
                            "-v",
                            "-c",
                            "-s",
                            "-d",
                            "history_test",
                            buildings_pbf,
                            "-U",
                            "postgres",
                            "-H",
                            "env-pgs-dev1",
                            "-S",
                            "dates.style",
                            "-p",
                            "ex_" + year_month + "_" + str(id),
                            "--extra-attributes"])
    if result.returncode == 0:
        print("Completed database import for {}".format(year_month))
        return 0
    else:
        result.check_returncode()
    
        

# 1) Get the city .poly file based on its ID
for id in city_relation_osm_ids:
    # Get city polygon file
    try:
        #city_output_poly_path = get_city_poly_file(id)
        city_output_poly_file = str(id) + ".poly"
        city_output_poly_path = city_polys_output_directory + os.sep + city_output_poly_file
    except Exception as ex:
        print("Exception raised getting city poly file: {}".format(ex))
        continue

    # Subset full history with city polygon
    try:
        #city_output_pbf_file = extract_city_from_history(id, city_output_poly_path)
        city_output_pbf_file = city_pbfs_output_directory + os.sep + str(id) + ".osm.pbf"
    except Exception as ex:
        print("Exception raised extracting city from history: {}".format(ex))
        continue

    # Get snapshots of city at 3 month intervals
    current_date = start_date
    while current_date < end_date:
        try:
            timed_city_output_pbf = snapshot_city_at_timestamp(city_output_pbf_file, current_date, id)
        except Exception as ex:
            print("Exception raised snapshotting {} at time {}: {}".format(str(id), str(current_date), ex))
            continue

        year_month = current_date.strftime("%Y_%m")

        # Extract buildings from timed snapshot
        try:
            buildings_pbf = extract_buildings_from_snapshot(timed_city_output_pbf, id)
        except Exception as ex:
            print("Exception raised extracting buildings from {}: {}".format(str(id), ex))
            continue
        
        # Import buildings into the database
        try:
            import_buildings_into_db(buildings_pbf, id)
        except Exception as ex:
            print("Exception raised importing buildings into database for {}:{}".format(str(id), ex))
            continue

        # Increment date by 3 months
        current_date = current_date + relativedelta(months=6)


    
