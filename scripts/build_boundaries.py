"""Reproduce small-scale map geometry from preserved Census boundaries. Requires GDAL."""
import pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
source='/vsizip/'+str(ROOT/'data/raw/cb_2025_us_cd119_500k.zip')
output=ROOT/'dist/data/districts.geojson'
subprocess.run(['ogrinfo','-so','-al',source],check=True)
# NAD83 -> WGS84 uses GDAL's normal coordinate operation selection. Cartographic use only.
subprocess.run(['ogr2ogr','-overwrite','-f','GeoJSON','-t_srs','EPSG:4326','-simplify','0.006','-lco','COORDINATE_PRECISION=5',str(output),source],check=True)
subprocess.run(['ogrinfo','-so','-al',str(output)],check=True)
