from django import forms
from django.contrib import admin
from django.conf import settings
from django.shortcuts import render

from dal import autocomplete
from taggit.forms import TagField

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from modeltranslation.admin import TabbedTranslationAdmin
from geonode.base.models import (
    TopicCategory,
    SpatialRepresentationType,
    Region,
    RestrictionCodeType,
    ContactRole,
    Link,
    License,
    HierarchicalKeyword,
    MenuPlaceholder,
    Menu,
    MenuItem,
    CuratedThumbnail,
    Configuration,
    Thesaurus, ThesaurusLabel, ThesaurusKeyword, ThesaurusKeywordLabel,
)

from geonode.base.forms import (
    BatchEditForm,
    BatchPermissionsForm,
    UserAndGroupPermissionsForm
)
from geonode.base.widgets import TaggitSelect2Custom

from csw_services.models import CswService


@admin.register(CswService)
class CswServiceAdmin(admin.ModelAdmin):
    fields = ('service_type', 'uuid', 'title', 'abstract',  'owner')

    list_display = ('id', 'service_type', 'uuid', 'title')
    list_display_links = ('id', 'uuid')
    ordering = ('service_type', 'title',)