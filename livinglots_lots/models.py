from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.measure import D
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from inplace.models import Place, PlaceManager
from livinglots import (get_lot_model, get_lot_model_name, get_lotgroup_model,
                        get_lotlayer_model, get_owner_model,
                        get_owner_model_name)

from .exceptions import ParcelAlreadyInLot


class BaseLotManager(PlaceManager):

    def create_lot_for_parcels(self, parcels, **lot_kwargs):
        lots = []

        # Check parcel validity
        for parcel in parcels:
            if parcel.lot_model.count():
                raise ParcelAlreadyInLot('Parcel %d is already part of a lot' % parcel.pk)

        # Create lots for each parcel
        # NB: Assumes parcels have these properties!
        for parcel in parcels:
            kwargs = {
                'parcel': parcel,
                'polygon': parcel.geom,
                'centroid': parcel.geom.centroid,
                'address_line1': parcel.street_address,
                'name': parcel.street_address,
                'postal_code': parcel.zip_code,
                'city': parcel.city,
                'state_province': parcel.state or 'CA',
            }
            kwargs.update(**lot_kwargs)

            # Create or get owner for parcels
            if parcel.owner_name:
                (owner, created) = get_owner_model().objects.get_or_create(
                    parcel.owner_name,
                    defaults={
                        'owner_type': parcel.owner_type,
                    }
                )
                kwargs['owner'] = owner

            lot = get_lot_model()(**kwargs)
            lot.save()
            lots.append(lot)

        # Multiple lots, create a lot group
        if len(lots) > 1:
            example_lot = lots[0]
            kwargs = {
                'address_line1': example_lot.address_line1,
                'name': example_lot.name,
            }
            kwargs.update(**lot_kwargs)
            lot = get_lotgroup_model()(**kwargs)
            lot.save()
            lot.update(lots=lots)
        return lot

    def get_visible(self):
        """
        Should be publicly viewable if:
            * There is no known use or its type is visible
            * The known_use_certainty is over 3
            * If any steward_projects exist, they opted in to being included
        """
        return super(BaseLotManager, self).get_query_set().filter(
            Q(
                Q(known_use__isnull=True) |
                Q(known_use__visible=True, steward_inclusion_opt_in=True)
            ),
            known_use_certainty__gt=3,
            group__isnull=True,
        )

    def find_nearby(self, lot, include_self=False, visible_only=True, miles=.5):
        """Find lots near the given lot."""
        if visible_only:
            qs = self.get_visible()
        else:
            qs = super(BaseLotManager, self).get_query_set()
        if not include_self:
            qs = qs.exclude(pk=lot.pk)
        return qs.filter(centroid__distance_lte=(lot.centroid, D(mi=miles)))


class VisibleLotManager(BaseLotManager):
    """A manager that only retrieves lots that are publicly viewable."""

    def get_query_set(self):
        return self.get_visible()


class BaseLot(Place):

    objects = BaseLotManager()
    visible = VisibleLotManager()

    owner = models.ForeignKey(get_owner_model_name(),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_('The owner of this lot.'),
        verbose_name=_('owner'),
    )

    known_use = models.ForeignKey('Use',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    known_use_certainty = models.PositiveIntegerField(_('known use certainty'),
        default=0,
        help_text=_('On a scale of 0 to 10, how certain are we that the known '
                    'use is correct?'),
    )
    known_use_locked = models.BooleanField(_('known use locked'),
        default=False,
        help_text=_('Is the known use field locked? If it is not, the site '
                    'will make a guess using available data. If you are '
                    'certain that the known use is correct, lock it.'),
    )

    added = models.DateTimeField(_('date added'),
        auto_now_add=True,
        help_text=('When this lot was added'),
    )

    added_reason = models.CharField(_('reason added'),
        max_length=256,
        help_text=('The original reason this lot was added'),
    )

    steward_inclusion_opt_in = models.BooleanField(_('steward inclusion opt-in'),
        default=False,
        help_text=_('Did the steward opt in to being included on our map?'),
    )

    polygon_area = models.DecimalField(_('polygon area'),
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('The area of the polygon in square feet'),
    )
    polygon_width = models.DecimalField(_('polygon width'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('The width of the polygon in feet'),
    )


    class Meta:
        abstract = True
        permissions = (
            ('view_all_details', 'Can view all details for lots'),
            ('view_all_filters', 'Can view all map filters for lots'),
            ('view_all_lots', 'Can view all lots'),
        )

    def __unicode__(self):
        return u'%s' % (self.address_line1,)

    def save(self, *args, **kwargs):
        super(BaseLot, self).save(*args, **kwargs)
        if get_lotlayer_model():
            self.check_layers()

    @models.permalink
    def get_absolute_url(self):
        return ('lots:lot_detail', (), { 'pk': self.pk, })

    def find_nearby(self, count=5):
        return self.__class__.objects.find_nearby(self)[:count]
    nearby = property(find_nearby)

    def calculate_known_use_certainty(self):
        """
        Calculate the certainty (0 to 10) that this lot's known use is
        accurate.
        """

        #
        # First, the data that indicate real certainty
        #

        # If someone told us what is happening here, known_use_locked should be
        # set. Similarly if we manually changed the use for any reason.
        if self.known_use_locked:
            return self.known_use_certainty

        #
        # Now for the fuzzy calculations
        #
        certainty = 0

        # TODO actual fuzzy calculations

        return min(certainty, 9)

    def _get_number_of_lots(self):
        try:
            return self.lotgroup.lot_set.count()
        except Exception:
            return 1
    number_of_lots = property(_get_number_of_lots)

    def _get_lots(self):
        try:
            return self.lotgroup.lot_set.all()
        except Exception:
            return [self,]
    lots = property(_get_lots)

    def _get_display_name(self):
        if self.name:
            return self.name
        elif self.address_line1:
            return self.address_line1
        else:
            return "%d (unknown address)" % self.pk
    display_name = property(_get_display_name)

    def _get_latitude(self):
        try:
            return self.centroid.y
        except Exception:
            return None
    latitude = property(_get_latitude)

    def _get_longitude(self):
        try:
            return self.centroid.x
        except Exception:
            return None
    longitude = property(_get_longitude)

    def _is_visible(self):
        return (
            (not self.known_use or
             (self.known_use.visible and self.steward_inclusion_opt_in)) and
            self.known_use_certainty > 3
        )
    is_visible = property(_is_visible)

    @models.permalink
    def get_geojson_url(self):
        """Override inplace url"""
        return ('lots:lot_detail_geojson', (), { 'pk': self.pk })

    @classmethod
    def get_filter(cls):
        """
        Get a filter class that follows the same conventions as the filter
        classes created with django-filter.
        """
        raise NotImplementedError('Implement BaseLot.get_filter')

    def check_layers(self):
        """
        Add lot to each lotlayer it should be part of, remove it from the ones
        it should not be part of.
        """
        # Clear lot's layers
        self.lotlayer_set.clear()

        # Get model classes
        lot_model = get_lot_model()
        lotlayer_model = get_lotlayer_model()

        # Check each layer to see if the lot is part of it
        layer_filters = lotlayer_model.get_layer_filters()
        for layer_name in layer_filters.keys():
            # If lot should be in layer, add it
            try:
                if lot_model.objects.filter(layer_filters[layer_name], pk=self.pk).exists():
                    layer, created = lotlayer_model.objects.get_or_create(name=layer_name)
                    self.lotlayer_set.add(layer)
            except Exception:
                pass


class BaseLotLayer(models.Model):
    """
    A grouping of lots often conceptualized as a "layer", or a set of lots that
    you might want to hide or show together.

    This can make queries more efficient. For example, you might have a layer
    named 'public' that contains all lots with public owners. This would avoid
    the necessity of joining the lots with multiple tables (eg, parcel, owner,
    owner type).
    """
    name = models.CharField(max_length=128, unique=True)
    lots = models.ManyToManyField(get_lot_model_name())

    @classmethod
    def get_layer_filters(cls):
        """
        Get a dictionary of layer names to a Q query definition for each of the
        lot layers.
        """
        raise NotImplementedError('Implement BaseLotLayer.get_layer_filters()')

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class BaseLotGroup(models.Model):
    """A group of lots."""

    def add(self, lot):
        """Add a lot to this group."""
        lots = set(list(self.lot_set.all()))
        lots.add(lot)
        self.update(lots=lots)

    def remove(self, lot):
        """Remove a lot from this group."""
        lots = list(self.lot_set.all())
        lots.remove(lot)
        self.update(lots=lots)

    def update(self, lots=None):
        """
        Update this group with the given lots. Allow lots to be passed
        manually since this might be called on a lot's pre_save signal.
        """

        if not lots:
            lots = self.lot_set.all()

        # Update lot_set
        self.lot_set.clear()
        self.lot_set.add(*lots)

        # Update polygon
        self.polygon = None
        for lot in lots:
            if not lot.polygon: continue
            if not self.polygon:
                self.polygon = lot.polygon
            else:
                union = self.polygon.union(lot.polygon)
                if not isinstance(union, MultiPolygon):
                    union = MultiPolygon([union])
                self.polygon = union

        # Update centroid
        self.centroid = self.polygon.centroid
        self.save()

    def __unicode__(self):
        return self.name or self.address_line1 or '%s' % self.pk

    class Meta:
        abstract = True


class Use(models.Model):
    """
    A way a lot could be used.
    """
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200)
    visible = models.BooleanField(_('visible'),
        default=True,
        help_text=_('Should lots with this use be visible on the map? If the '
                    'use is not vacant and not a project that someone could '
                    'join, probably not.'),
    )

    def __unicode__(self):
        return self.name


from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=BaseLot)
def save_lot_update_group(sender, instance=None, **kwargs):
    """Update the group that this member is part of."""
    if not instance: return

    # Try to get the group this instance was part of, if any
    try:
        previous_group = get_lot_model().objects.get(pk=instance.pk).group
    except Exception:
        previous_group = None

    # Get the group this instance will be part of, if any
    next_group = instance.group

    # If instance was in a group before but no longer will be, update that
    # group accordingly
    if previous_group and previous_group != next_group:
        previous_group.remove(instance)

    # If instance was not in a group before but will be, update that group
    if next_group and next_group != previous_group:
        next_group.add(instance)


@receiver(post_delete, sender=BaseLot)
def delete_lot_update_group(sender, instance=None, **kwargs):
    """Update the group this lot was part of to show that it was deleted."""
    if instance.group:
        instance.group.update()
