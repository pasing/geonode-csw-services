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

    # uuid = models.CharField(max_length=64, null=False)
    #
    # title = models.CharField(
    #     _('title'),
    #     max_length=255,
    #     help_text=_('name by which the cited resource is known'),
    # )
    #
    # abstract = models.TextField(
    #     _('abstract'),
    #     max_length=2000,
    #     blank=True,
    #     help_text=ResourceBase.abstract_help_text,
    # )
    #
    # poc = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     blank=True,
    #     null=False,
    #     related_name='owned_resource',
    #     verbose_name=_("Point of Contact"),
    # )
    #
    # owner = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     blank=True,
    #     null=False,
    #     related_name='owned_resource',
    #     verbose_name=_("Owner"),
    # )

    class Meta(ResourceBase.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(CswService, self).__init__(*args, **kwargs)

    def get_upload_session(self):
        raise NotImplementedError()


def pre_save_service(instance, sender, **kwargs):
    # if kwargs.get('raw', False):
    #     try:
    #         _resourcebase_ptr = instance.resourcebase_ptr
    #         instance.owner = _resourcebase_ptr.owner
    #         instance.uuid = _resourcebase_ptr.uuid
    #         instance.bbox_polygon = _resourcebase_ptr.bbox_polygon
    #         instance.srid = _resourcebase_ptr.srid
    #     except Exception as e:
    #         LOGGER.exception(e)

    instance.csw_type = 'service'

    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'
    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    # # Set a default user for accountstream to work correctly.
    # if instance.owner is None:
    #     instance.owner = get_valid_user()

    # logger.debug("handling UUID In pre_save_layer")
    # if hasattr(settings, 'LAYER_UUID_HANDLER') and settings.LAYER_UUID_HANDLER != '':
    #     logger.debug("using custom uuid handler In pre_save_layer")
    #     from geonode.layers.utils import get_uuid_handler
    #     instance.uuid = get_uuid_handler()(instance).create_uuid()
    # else:
    #     if instance.uuid == '':
    #         instance.uuid = str(uuid.uuid1())

    # logger.debug("In pre_save_layer")
    # if instance.alternate is None:
    #     instance.alternate = _get_alternate_name(instance)
    # logger.debug("instance.alternate is: {}".format(instance.alternate))

    # base_file, info = instance.get_base_file()

    # if info:
    #     instance.info = info
    #
    # if base_file is not None:
    #     extension = '.%s' % base_file.name
    #     if extension in vec_exts:
    #         instance.storeType = 'dataStore'
    #     elif extension in cov_exts:
    #         instance.storeType = 'coverageStore'

    if instance.bbox_polygon is None:
        instance.set_bbox_polygon((-180, -90, 180, 90), 'EPSG:4326')
    instance.set_bounds_from_bbox(
        instance.bbox_polygon,
        instance.bbox_polygon.srid
    )
    # # Send a notification when a layer is created
    # if instance.pk is None and instance.title:
    #     # Resource Created
    #     notice_type_label = '%s_created' % instance.class_name.lower()
    #     recipients = get_notification_recipients(notice_type_label, resource=instance)
    #     send_notification(recipients, notice_type_label, {'resource': instance})


def pre_delete_service(instance, sender, **kwargs):
    remove_object_permissions(instance)

    # """
    # Remove any associated style to the layer, if it is not used by other layers.
    # Default style will be deleted in post_delete_layer
    # """
    # if instance.remote_service is not None and instance.remote_service.method == INDEXED:
    #     # we need to delete the maplayers here because in the post save layer.remote_service is not available anymore
    #     # REFACTOR
    #     from geonode.maps.models import MapLayer
    #     logger.debug(
    #         "Going to delete associated maplayers for [%s]",
    #         instance.alternate)
    #     MapLayer.objects.filter(
    #         name=instance.alternate,
    #         ows_url=instance.ows_url).delete()
    #     return
    #
    # LOGGER.debug(
    #     "Going to delete the styles associated for [%s]",
    #     instance.alternate)
    # ct = ContentType.objects.get_for_model(instance)
    # OverallRating.objects.filter(
    #     content_type=ct,
    #     object_id=instance.id).delete()
    #
    # default_style = instance.default_style
    # for style in instance.styles.all():
    #     if style.layer_styles.all().count() == 1:
    #         if style != default_style:
    #             style.delete()
    #
    # # Delete object permissions
    # remove_object_permissions(instance)


def post_delete_service(instance, sender, **kwargs):
    pass
    # """
    # Removed the layer from any associated map, if any.
    # Remove the layer default style.
    # """
    # if instance.remote_service is not None and instance.remote_service.method == INDEXED:
    #     return
    #
    # from geonode.maps.models import MapLayer
    # logger.debug(
    #     "Going to delete associated maplayers for [%s]", instance.name)
    # MapLayer.objects.filter(
    #     name=instance.alternate,
    #     ows_url=instance.ows_url).delete()
    #
    # logger.debug(
    #     "Going to delete the default style for [%s]", instance.name)
    #
    # if instance.default_style and Layer.objects.filter(
    #         default_style__id=instance.default_style.id).count() == 0:
    #     instance.default_style.delete()
    #
    # try:
    #     if instance.upload_session:
    #         for lf in instance.upload_session.layerfile_set.all():
    #             lf.file.delete()
    #         instance.upload_session.delete()
    # except UploadSession.DoesNotExist:
    #     pass


# def catalogue_pre_delete(instance, sender, **kwargs):
#     """Removes the layer from the catalogue"""
#     catalogue = get_catalogue()
#     catalogue.remove_record(instance.uuid)


def post_save_service(instance, sender, **kwargs):
    """Get information from catalogue"""
    resources = ResourceBase.objects.filter(id=instance.resourcebase_ptr.id)
    LOGGER.warn(f'*** POST SAVING SERVICE "{instance.uuid}"')

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

    resources.update(
        metadata_xml=md_doc,
        csw_anytext=csw_anytext)


def create_metadata_document(instance, template):
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    tpl = get_template(template)
    ctx = {
        'service': instance,
        'SITEURL': site_url,
        }
           # 'LICENSES_METADATA': getattr(settings,
           #                              'LICENSES',
           #                              dict()).get('METADATA',
           #                                          'never')}
    md_doc = tpl.render(context=ctx)
    return md_doc


if 'geonode.catalogue' in settings.INSTALLED_APPS:
    signals.pre_save.connect(pre_save_service, sender=CswService)
    signals.post_save.connect(post_save_service, sender=CswService)
    # signals.pre_delete.connect(catalogue_pre_delete, sender=Service)
    # signals.pre_delete.connect(catalogue_pre_delete, sender=Document)

