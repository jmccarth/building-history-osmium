import os
import subprocess
import requests
import datetime
from dateutil.relativedelta import relativedelta


# Steps 0X should only need to be run once for any major geographic region
# They are designed to let you spatially filter the planet history file down 
# somewhat to make queries that follow faster.

# 0A) Fill in the following configuration parameters
osm_history_file_path = r"data/history-latest.osm.pbf"
# osm_history_buildings_only_file_path = r"data/buildings-history-latest.osm.pbf"
# subset_poly_path = r"data/north-america.poly"
# subset_osm_output_path = r"data/outputs/north-america.osm.pbf"
city_polys_output_directory = r"data/outputs/citypolys"
city_pbfs_output_directory = r"data/outputs/citypbfs"
city_relation_osm_ids = [2062154,7486330]
start_date = datetime.datetime(2000,1,1,0,0,0)
end_date = datetime.datetime.now()

# 1) Get the city .poly file based on its ID
for id in city_relation_osm_ids:
    print("Attempting to get .poly file for relation {}...".format(str(id)))
    r = requests.get("http://polygons.openstreetmap.fr/get_poly.py?id={}&params=0".format(str(id)))
    print("Request returned with code {}".format(r.status_code))
    if r.status_code == 200:
        city_output_poly_file = str(id) + ".poly"
        city_output_poly_path = city_polys_output_directory + os.sep + city_output_poly_file
        file = open(city_output_poly_path,"w")
        file.write (r.text)
        file.close()
        
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
        print("Completed extracting city {} to {}".format(str(id),city_output_pbf_file))

        # 2) Filter city level data by timestamp
    current_date = start_date
    while current_date < end_date:
        timestamp = current_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        year_month = current_date.strftime("%Y_%m")
        timed_city_output_pbf = city_pbfs_output_directory + os.sep + str(id) + "." + year_month + ".osm.pbf"
        print("Filtering for {}".format(timestamp))
        result = subprocess.run(["osmium",
                                "time-filter",
                                city_output_pbf_file,
                                timestamp,
                                "--overwrite",
                                "-o",
                                timed_city_output_pbf])
        print("Completed temporal filter: {}".format(timed_city_output_pbf))

        # 3) Extract buildings
        buildings_pbf = city_pbfs_output_directory + os.sep + str(id) + "." + year_month + ".buildings" + ".osm.pbf"
        print("Filtering {} for buildings".format(timed_city_output_pbf))
        result = subprocess.run(["osmium",
                                "tags-filter",
                                timed_city_output_pbf,
                                "building",
                                "-o",
                                buildings_pbf])
        print("Buildings filtered to {}".format(buildings_pbf))

        # 4) import into database
        print("Importing into database...")
        result = subprocess.run(["osm2pgsql",
                                "-v",
                                "-c",
                                "-s",
                                "-d",
                                "history_test",
                                buildings_pbf,
                                "-U",
                                "osmimport",
                                "-H",
                                "env-pgs-dev1",
                                "-S",
                                "dates.style",
                                "-p",
                                "ex_" + year_month + "_" + str(id),
                                "--extra-attributes"])
        print(">>>>>>>>>>>> {}".format(result.args))
        print("Completed database import for {}".format(year_month))
        # increment the date by 3 months
        current_date = current_date + relativedelta(months=3)
    else:
        print("Error retrieving city polygon for {}. Skipping.".format(str(id)))

    
