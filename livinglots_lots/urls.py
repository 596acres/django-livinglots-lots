from django.conf.urls import url

from .views import (AddToGroupView, CheckLotWithParcelExistsView,
                    CountWatchersView, CreateLotByGeomView, EmailWatchersView,
                    HideLotView, HideLotSuccessView, LotDetailView,
                    LotGeoJSONDetailView, LotsGeoJSON, LotsGeoJSONPolygon,
                    LotsGeoJSONCentroid, LotsCountView, LotsCountBoundaryView,
                    LotsCSV, LotsKML, RemoveFromGroupView)


urlpatterns = [
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

    url(r'^(?P<pk>\d+)/hide/$', HideLotView.as_view(),
        name='hide_lot'),
    url(r'^(?P<pk>\d+)/hide/success/$', HideLotSuccessView.as_view(),
        name='hide_lot_success'),

    url(r'^create/by-parcels/check-parcel/(?P<pk>\d+)/$',
        CheckLotWithParcelExistsView.as_view(),
        name='create_by_parcels_check_parcel'),

    url(r'^create/by-geom/$',
        CreateLotByGeomView.as_view(),
        name='create_by_geom'),

    url(r'^(?P<pk>\d+)/group/add/$', AddToGroupView.as_view(),
        name='add_to_group'),
    url(r'^(?P<pk>\d+)/group/remove/$', RemoveFromGroupView.as_view(),
        name='remove_from_group'),

    url(r'^organize/watchers/email/', EmailWatchersView.as_view(),
        name='lot_email_watchers'),
    url(r'^organize/watchers/count/', CountWatchersView.as_view(),
        name='lot_count_watchers'),
]
