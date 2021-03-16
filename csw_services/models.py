from enum import Enum
import errno
import logging
from lxml import etree
from defusedxml import lxml as dlxml

from django.db import models
from django.db.models import signals
from django.conf import settings
from django.dispatch import receiver
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _


from geonode.base.models import ResourceBase
from geonode.catalogue import get_catalogue

LOGGER = logging.getLogger(__name__)


class ServiceType(Enum):
    WMS = "OGC:WMS"
    WCS = "OGC:WCS"
    WFS = "OGC:WFS"
    WMTS = "OGC:WMTS"
    OTHER = "OTHER"

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class CswService(ResourceBase):

    service_type = models.CharField(
        max_length=32,
        choices=ServiceType.choices(),
        null=False)

    class Meta(ResourceBase.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(CswService, self).__init__(*args, **kwargs)

    def get_upload_session(self):
        raise NotImplementedError()


def pre_save_service(instance, sender, **kwargs):

    instance.csw_type = 'service'

    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'
    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    if instance.bbox_polygon is None:
        instance.set_bbox_polygon((-180, -90, 180, 90), 'EPSG:4326')
    instance.set_bounds_from_bbox(
        instance.bbox_polygon,
        instance.bbox_polygon.srid
    )

def pre_delete_service(instance, sender, **kwargs):
    remove_object_permissions(instance)

def post_delete_service(instance, sender, **kwargs):
    pass


def post_save_service(instance, sender, **kwargs):
    """Get information from catalogue"""
    resources = ResourceBase.objects.filter(id=instance.resourcebase_ptr.id)
    LOGGER.warn(f'*** POST SAVING SERVICE "{instance.uuid}"')
    if resources.exists() and resources.count() == 1:
        # Update the Catalog
        try:
            catalogue = get_catalogue()
            catalogue.create_record(instance)
            record = catalogue.get_record(instance.uuid)
        except EnvironmentError as err:
            if err.errno == errno.ECONNREFUSED:
                LOGGER.warning(f'Could not connect to catalogue to save information for layer "{instance.name}"', err)
                return
            else:
                raise err

        if not record:
            LOGGER.exception(f'Metadata record for service {instance.title} does not exist, check the catalogue signals.')
            return

        # generate an XML document
        if instance.metadata_uploaded and instance.metadata_uploaded_preserve:
            md_doc = etree.tostring(dlxml.fromstring(instance.metadata_xml))
        else:
            LOGGER.info(f'Rebuilding metadata document for "{instance.uuid}"')
            template = getattr(settings, 'CATALOG_SERVICE_METADATA_TEMPLATE', 'xml/service-template.xml')
            md_doc = create_metadata_document(instance, template)
        try:
            csw_anytext = catalogue.catalogue.csw_gen_anytext(md_doc)
        except Exception as e:
            LOGGER.exception(e)
            csw_anytext = ''

        r = resources.get()
        r.set_workflow_perms(approved=True, published=True)

        resources.update(
            metadata_xml=md_doc,
            csw_anytext=csw_anytext)
    else:
        LOGGER.warn(f'*** The resource selected does not exists or or more than one is selected "{instance.uuid}"')


def create_metadata_document(instance, template):
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    tpl = get_template(template)
    ctx = {
        'service': instance,
        'SITEURL': site_url,
        }
    md_doc = tpl.render(context=ctx)
    return md_doc


if 'geonode.catalogue' in settings.INSTALLED_APPS:
    signals.pre_save.connect(pre_save_service, sender=CswService)
    signals.post_save.connect(post_save_service, sender=CswService)
