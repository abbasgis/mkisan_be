from api.enums import APIEnum


class AccessibilityType(APIEnum):
    File = 'File'
    DB = 'Database'
    D_DB = 'Django Database Key'


class DataModel(APIEnum):
    R = 'Raster'
    V = 'Vector'


class VectorModel(APIEnum):
    T = 'TIN'
    N = 'Network'
    Geom = 'Geometry'
    Cnt = 'Contour'
    Oth = 'Other'


class RasterModel(APIEnum):
    S = 'Satellite'
    DEM = 'Digital Elevation Model'
    DSM = 'Digital Surface Model'
    Surf = 'Surface'
    Classification = 'Classification'
    Oth = 'Oth'
