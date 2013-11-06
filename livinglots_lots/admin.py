from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from livinglots import get_lot_model, get_lotgroup_model

from .admin_views import AddToGroupView
from .models import Use


class LotAdmin(OSMGeoAdmin):
    actions = ('add_to_group',)
    list_display = ('address_line1', 'city', 'name', 'known_use',)
    list_filter = ('known_use',)
    readonly_fields = ('added',)
    search_fields = ('address_line1', 'name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'address_line1', 'address_line2', 'city',
                       'state_province', 'postal_code', 'added', 'group',),
        }),
        ('Known use', {
            'fields': ('known_use', 'known_use_certainty',
                       'known_use_locked',),
        }),
        ('Stewards', {
            'fields': ('steward_inclusion_opt_in',),
        }),
        ('Other data', {
            'classes': ('collapse',),
            'fields': ('polygon_area', 'polygon_width',),
        }),
        ('Geography', {
            'classes': ('collapse',),
            'fields': ('centroid', 'polygon',),
        }),
    )

    def add_to_group(self, request, queryset):
        ids = queryset.values_list('pk', flat=True)
        ids = [str(id) for id in ids]
        return HttpResponseRedirect(reverse('admin:lots_lot_add_to_group') +
                                    '?ids=%s' % (','.join(ids)))

    def get_urls(self):
        opts = self.model._meta
        app_label, object_name = (opts.app_label, opts.object_name.lower())
        prefix = "%s_%s" % (app_label, object_name)

        urls = super(LotAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^add-to-group/', AddToGroupView.as_view(),
                name='%s_add_to_group' % prefix),
        )
        return my_urls + urls


class LotInlineAdmin(admin.TabularInline):
    model = get_lot_model()

    extra = 0
    fields = ('address_line1', 'name',)
    readonly_fields = ('address_line1', 'name',)
    template = 'admin/lots/lot/edit_inline/tabular.html'


class LotGroupAdmin(LotAdmin):
    inlines = (LotInlineAdmin,)


class UseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',),}


admin.site.register(get_lot_model(), LotAdmin)
admin.site.register(get_lotgroup_model(), LotGroupAdmin)
admin.site.register(Use, UseAdmin)
