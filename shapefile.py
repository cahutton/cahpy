"""TODO."""

from osgeo.ogr import Open
# from psycopg2.sql import Identifier, Literal, SQL

from cahpy.log import ObjectWithLogger
from cahpy.postgresql import Postgresql


class Shapefile(ObjectWithLogger):
    """TODO."""

    LOGGER_NAME = 'Shapefile'
    TYPE_MAP = {
        'Real': 'NUMERIC',
        'String': 'TEXT'
    }

    def __init__(self, filePath, readOnly=True, postgresql=None,
                 fields=None):
        """TODO."""
        self.LOGGER_NAME = str(filePath)

        super().__init__()

        self.dataset = Open(str(filePath), int(not readOnly))
        self.layerDefinition = self.dataset.GetLayer(0).GetLayerDefn()
        self.fields = self.getFields()
        self.postgresql = postgresql or Postgresql()

    def getDdl(self, tableName, schemaName='public', comment=None):
        """TODO."""
        return [self.postgresql.dropTable(tableName, schemaName=schemaName,
                                          getString=True)] \
            + self.postgresql.createTable(tableName, [
                {
                    # TODO: 'constraints': [],
                    'name': columnName,
                    'notNull': True,
                    'type': self.TYPE_MAP.get(columnType)
                } for columnName, columnType in self.getFields()
            ], schemaName=schemaName, comment=comment, getString=True)

    def getFields(self):
        """TODO."""
        return self.fields if hasattr(self, 'fields') else [
            (self.layerDefinition.GetFieldDefn(field).GetName(),
             self.layerDefinition.GetFieldDefn(field).GetFieldTypeName(
                self.layerDefinition.GetFieldDefn(field).GetType()))
            for field in range(self.layerDefinition.GetFieldCount())
        ]

    # def getGeoJson(self, geometry):
    #     return geometry.ExportToJson()

    # def getProjection(self):
    #     # from osgeo import osr
    #     # from Layer
    #     layer = dataset.GetLayer()
    #     spatialRef = layer.GetSpatialRef()
    #     # from Geometry
    #     feature = layer.GetNextFeature()
    #     geom = feature.GetGeometryRef()
    #     spatialRef = geom.GetSpatialReference()

    def getWkt(self, geometry):
        """TODO."""
        # geometry.GetGeometryName() == 'MULTIPOLYGON'
        return geometry.ExportToWkt()

    def importData(self, tableName, schemaName):
        """TODO."""
        layer = self.dataset.GetLayer(0)
        columnNames = [
            fieldName for fieldName, fieldType in self.fields
        ] + ['geometry']

        for i in range(layer.GetFeatureCount()):
            feature = layer.GetFeature(i)

            values = [
                feature.GetField(j)
                for j in range(self.layerDefinition.GetFieldCount())
            ] + ['ST_GeometryFromText(%s, 4326)'
                 % self.getWkt(feature.GetGeometryRef())]

            self.postgresql.insertValues(
                tableName, values, schemaName=schemaName,
                columnNames=columnNames)
