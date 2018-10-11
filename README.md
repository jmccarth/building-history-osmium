# Building History Osmium

This script uses the [Osmium Tool](https://osmcode.org/osmium-tool/) to perform a specific history filtering option. It was designed to study historical progression of OpenStreetMap (OSM) contributions by generating snapshots of the OpenStreetMap dataset for specified locations and times and importing them into a PostgreSQL database.

## Getting Started

### Prerequisites

* Python 3

In its infancy, this script just runs shell commands so it assumes that the following tools are installed and executable by the user running the python script:

* osmium-tool
* osm2pgsql

In addition, you need to have a PostGIS database set up and ready to go, and you need to download a copy of the [Planet OSM History File](https://planet.openstreetmap.org/planet/full-history/) in PBF format.

### Installing

Clone this repository to your local machine and make sure you have the required data to begin with.

## Usage

For now, you need to modify the script manually to set relevant paths to datasets. You can specify what city/cities to extract data for by populating the ```city_relation_osm_ids``` variable with the OSM relation IDs of the cities you are interested in. For example, this command will generate data for Waterloo and Stratford, Ontario, Canada.

```python
city_relation_osm_ids = [2062154,7486330]
```

You can specify the start and end dates by setting the following variables to Python datetimes:

```python
start_date = datetime.datetime(2000,1,1,0,0,0)
end_date = datetime.datetime.now()
```

Data will be generated in 3 month intervals.

Note that the initial step of subsetting the history file based on a city relation can take 1-2 hours depending on your hardware. The rest of the steps should happen relatively quickly.

## Contributing

Feel free to reach out with ideas or open a PR. This repo is just getting started.

## License

This software is licensed under the MIT licnece. No warranty or support is provided. See LICENSE.md for the details of the licence.