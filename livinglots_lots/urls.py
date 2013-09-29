from django.conf.urls.defaults import patterns, url

from .views import (LotDetailView, LotGeoJSONDetailView, LotsGeoJSON,
                    LotsGeoJSONPolygon, LotsGeoJSONCentroid, LotsCountView,
                    LotsCountBoundaryView, LotsCSV, LotsKML)


urlpatterns = patterns('',
    url(r'^csv/', LotsCSV.as_view(), name='csv'),
    url(r'^geojson/', LotsGeoJSON.as_view(), name='geojson'),
    url(r'^kml/', LotsKML.as_view(), name='kml'),
    url(r'^geojson-polygon/', LotsGeoJSONPolygon.as_view(),
        name='lot_geojson_polygon'),
    url(r'^geojson-centroid/', LotsGeoJSONCentroid.as_view(),
        name='lot_geojson_centroid'),
    url(r'^count/', LotsCountView.as_view(), name='lot_count'),
    url(r'^count-by-boundary/', LotsCountBoundaryView.as_view(),
        name='lot_count_by_boundary'),

    url(r'^(?P<pk>\d+)/$', LotDetailView.as_view(), name='lot_detail'),
    url(r'^(?P<pk>\d+)/geojson/$', LotGeoJSONDetailView.as_view(),
        name='lot_detail_geojson'),
)
