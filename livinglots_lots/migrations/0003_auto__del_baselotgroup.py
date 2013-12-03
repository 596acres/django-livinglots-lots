# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'BaseLotGroup'
        db.delete_table(u'livinglots_lots_baselotgroup')


    def backwards(self, orm):
        # Adding model 'BaseLotGroup'
        db.create_table(u'livinglots_lots_baselotgroup', (
            ('address_line2', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('polygon_width', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('address_line1', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('steward_inclusion_opt_in', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('polygon_area', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=15, decimal_places=2, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('known_use', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['livinglots_lots.Use'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('state_province', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('centroid', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True, blank=True)),
            ('known_use_locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['owners.Owner'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('polygon', self.gf('django.contrib.gis.db.models.fields.MultiPolygonField')(null=True, blank=True)),
            ('known_use_certainty', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('added_reason', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
        ))
        db.send_create_signal(u'livinglots_lots', ['BaseLotGroup'])


    models = {
        u'livinglots_lots.use': {
            'Meta': {'object_name': 'Use'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['livinglots_lots']