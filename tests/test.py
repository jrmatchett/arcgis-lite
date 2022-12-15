from arcgis_lite import *
from pprint import pprint as pp
import datetime

client_id = '4iztX6T7cBpdtwi6'

# gis = PortalGIS('https://maps.rcview.redcross.org/portal', client_id)

# fl1 = FeatureLayer('https://hosting.rcview.redcross.org/arcgis/rest/services/Hosted/Congregate_Shelters_List/FeatureServer/0', gis)
# fs1 = fl1.query(outFields='objectid,site_name,dr_number,city,state,clients,date_modified')
# gdf1 = fs1.gdf

#fl1 = FeatureLayer('https://hosting.rcview.redcross.org/arcgis/rest/services/Hosted/pacific_division_resources/FeatureServer/1', gis)
#q1 = fl1.query("state = 'HI'", outFields='state,county,fips')


#fl2 = FeatureLayer('https://ags.rcview.redcross.org/arcgis/rest/services/NSS/ShelterFacilityManager/FeatureServer/1', gis)
#q2 = fl2.query(outFields='shelternumber,buildingname,City,County,State,Post_Impact_Capacity')

fl3 = FeatureLayer('https://hosting.rcview.redcross.org/arcgis/rest/services/Hosted/Master_RC_Geo_FY22_2021/FeatureServer/0')
q3 = fl3.query("division = 'Pacific Division'")


#agol_gis = AgolGIS('jrmatchett', 'Ua7QXz&8AV', 'https://jrmatchett.maps.arcgis.com/')
# fl4 = agol_gis.feature_layer('8aff1cc77db8475ea83377894c4b36bf')   # wildfire reports


#fl5 = FeatureLayer('https://hosting.rcview.redcross.org/arcgis/rest/services/Hosted/congregate_shelters_dev/FeatureServer/0', gis)

# new_features = [
#     {
#         'attributes': {'site_name': 'Test 1', 'clients': 20, 'date_modified': int(datetime.datetime.now().timestamp() * 1000)},
#         'geometry': {'x': 0.0, 'y': 0.0, 'spatialReference': {'wkid': 4326}}
#     },
#     {
#         'attributes': {'site_name': 'Test 2', 'clients': 100, 'date_modified': int(datetime.datetime.now().timestamp() * 1000)},
#         'geometry': {'x': 0.001, 'y': 0.001, 'spatialReference': {'wkid': 4326}}
#     },
# ]

adds = ['5120 CA-140, Mariposa, CA 95338', '40233 Enterprise Dr, Oakhurst, CA 93644', '1579 Martin Luther King Jr Way, Merced, CA 95340']
