from datetime import date
import geojson
import json

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin

from inplace.boundaries.models import Boundary
from inplace.views import (GeoJSONListView, GeoJSONResponseMixin, KMLView,
                           PlacesDetailView)
from livinglots_genericviews import CSVView, JSONResponseView


#
# Helper mixins
#

class FilteredLotsMixin(object):
    """A mixin that makes it easy to filter on Lots using a LotResource."""

    def get_lots(self):
        # Give the user a different set of lots based on their permissions
        if self.request.user.has_perm('lots.view_all_lots'):
            resource = LotResource()
        else:
            resource = VisibleLotResource()
        orm_filters = resource.build_filters(filters=self.request.GET)
        return resource.apply_filters(self.request, orm_filters)


class LotContextMixin(ContextMixin):

    def get_lot(self):
        """Get the lot referred to by the incoming request"""
        try:
            if self.request.user.has_perm('lots.view_all_lots'):
                return Lot.objects.get(pk=self.kwargs['pk'])
            return Lot.visible.get(pk=self.kwargs['pk'])
        except Lot.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super(LotContextMixin, self).get_context_data(**kwargs)
        context['lot'] = self.get_lot()
        return context


class LotAddGenericMixin(FormMixin):
    """
    A mixin that eases adding content that references a single lot using
    generic relationships.
    """

    def get_initial(self):
        """Add initial content_type and object_id to the form"""
        initial = super(LotAddGenericMixin, self).get_initial()
        try:
            object_id = self.kwargs['pk']
        except KeyError:
            raise Http404
        initial.update({
            'content_type': ContentType.objects.get_for_model(Lot),
            'object_id': object_id,
        })
        return initial


class LotFieldsMixin(object):
    """
    A mixin that makes it easier to add a lot's fields to the view's output.
    """
    def get_fields(self):
        return self.fields

    def get_field_owner(self, lot):
        return lot.owner.name

    def get_field_owner_type(self, lot):
        return lot.owner.get_owner_type_display()

    def get_field_known_use(self, lot):
        return lot.known_use.name

    def _field_value(self, lot, field):
        try:
            # Call get_field_<field>()
            return getattr(self, 'get_field_%s' % field)(lot)
        except AttributeError:
            try:
                # Else try to get the property from the model instance
                return getattr(lot, field)
            except AttributeError:
                return None

    def _as_dict(self, lot):
        return dict([(f, self._field_value(lot, f)) for f in self.fields])


class LotGeoJSONMixin(object):

    def get_feature(self, lot):
        if lot.known_use:
            layer = 'in use'
        elif lot.owner and lot.owner.owner_type == 'public':
            layer = 'public'
        elif lot.owner and lot.owner.owner_type == 'private':
            layer = 'private'
        else:
            layer = ''

        try:
            lot_geojson = lot.geojson
        except Exception:
            if lot.polygon:
                lot_geojson = lot.polygon.geojson
            else:
                lot_geojson = lot.centroid.geojson
        return geojson.Feature(
            lot.pk,
            geometry=json.loads(lot_geojson),
            properties={
                'pk': lot.pk,
                'layer': layer,
            },
        )


#
# Export views
#

class LotsCSV(LotFieldsMixin, FilteredLotsMixin, CSVView):
    fields = ('address_line1', 'city', 'state_province', 'postal_code',
              'latitude', 'longitude', 'known_use', 'owner', 'owner_type',)

    def get_filename(self):
        return 'Grounded lots %s' % date.today().strftime('%Y-%m-%d')

    def get_rows(self):
        for lot in self.get_lots():
            yield self._as_dict(lot)


class LotsKML(LotFieldsMixin, FilteredLotsMixin, KMLView):
    fields = ('address_line1', 'city', 'state_province', 'postal_code',
              'known_use', 'owner', 'owner_type',)

    def get_filename(self):
        return 'Grounded lots %s' % date.today().strftime('%Y-%m-%d')

    def get_context_data(self, **kwargs):
        return {
            'places': self.get_lots().kml(),
            'download': True,
            'filename': self.get_filename(),
        }

    def render_to_response(self, context):
        return super(LotsKML, self).render_to_response(context)


class LotsGeoJSON(LotFieldsMixin, FilteredLotsMixin, GeoJSONResponseMixin,
                  JSONResponseView):
    fields = ('address_line1', 'city', 'state_province', 'postal_code',
              'known_use', 'owner', 'owner_type',)

    def get_context_data(self, **kwargs):
        return self.get_feature_collection()

    def get_feature(self, lot):
        return geojson.Feature(
            lot.pk,
            geometry=json.loads(lot.centroid.geojson),
            properties=self._as_dict(lot),
        )

    def get_filename(self):
        return 'Grounded lots %s' % date.today().strftime('%Y-%m-%d')

    def get_queryset(self):
        return self.get_lots()

    def render_to_response(self, context):
        response = super(LotsGeoJSON, self).render_to_response(context)
        if self.request.GET.get('download', 'no') == 'yes':
            response['Content-Disposition'] = ('attachment; filename="%s.json"' %
                                               self.get_filename())
        return response


class LotsGeoJSONPolygon(LotGeoJSONMixin, FilteredLotsMixin, GeoJSONListView):

    def get_queryset(self):
        return self.get_lots().filter(polygon__isnull=False).geojson(
            field_name='polygon',
            precision=8,
        ).select_related('known_use', 'owner__owner_type')


class LotsGeoJSONCentroid(LotGeoJSONMixin, FilteredLotsMixin, GeoJSONListView):

    def get_queryset(self):
        return self.get_lots().filter(centroid__isnull=False).geojson(
            field_name='centroid',
            precision=8,
        ).select_related('known_use', 'owner__owner_type')


#
# Counting views
#

class LotsCountView(FilteredLotsMixin, JSONResponseView):

    def get_context_data(self, **kwargs):
        lots = self.get_lots()
        context = {
            'lots-count': lots.count(),
            'no-known-use-count': lots.filter(known_use__isnull=True).count(),
            'in-use-count': lots.filter(
                known_use__isnull=False,
                known_use__visible=True,
            ).count(),
        }
        return context


class LotsCountBoundaryView(JSONResponseView):

    def get_context_data(self, **kwargs):
        return self.get_counts()

    def get_lot_resource(self):
        if self.request.user.has_perm('lots.view_all_lots'):
            return LotResource()
        return VisibleLotResource()

    def get_counts(self):
        boundary_layer = self.request.GET.get('choropleth_boundary_layer', '')
        lot_resource = self.get_lot_resource()
        filters = lot_resource.build_filters(filters=self.request.GET)

        try:
            # Ignore bbox
            del filters['centroid__within']
        except Exception:
            pass

        lots = lot_resource.apply_filters(self.request, filters)

        boundaries = Boundary.objects.filter(
            layer__name=boundary_layer,
        )

        counts = {}
        for boundary in boundaries:
            counts[boundary.label] = lots.filter(
                centroid__within=boundary.simplified_geometry
            ).count()
        return counts


class LotsMap(TemplateView):
    template_name = 'lots/map.html'

    def get_context_data(self, **kwargs):
        context = super(LotsMap, self).get_context_data(**kwargs)
        context.update({
            'filters': FiltersForm(),
            'uses': Use.objects.all().order_by('name'),
        })
        return context


#
# Detail views
#

class LotDetailView(PlacesDetailView):
    model = Lot

    def get_object(self):
        lot = super(LotDetailView, self).get_object()
        if not (lot.is_visible or self.request.user.has_perm('lots.view_all_lots')):
            raise Http404
        return lot

    def get(self, request, *args, **kwargs):
        # Redirect to the lot's group, if it has one
        self.object = self.get_object()
        if self.object.group:
            messages.info(request, _("The lot you requested is part of a "
                                     "group. Here is the group's page."))
            return HttpResponseRedirect(self.object.group.get_absolute_url())
        return super(LotDetailView, self).get(request, *args, **kwargs)


class LotGeoJSONDetailView(LotGeoJSONMixin, GeoJSONListView):
    model = Lot

    def get_queryset(self):
        lot = get_object_or_404(self.model, pk=self.kwargs['pk'])
        return self.model.objects.find_nearby(lot, include_self=True, miles=.1)

