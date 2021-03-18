# geonode-csw_services

Geonode-csw_services is a Django App to let GeoNode handle some service metadata for the exposed GeoServer services.

-----

## Configuration

1. Install the application as requirement:

       pip install -e git+https://github.com/geosolutions-it/geonode-csw_services@master#egg=csw_services

1. Add "csw_services" to your INSTALLED_APPS setting like this::

       INSTALLED_APPS = [
          'csw_services',
          ...
       ]
 
   If you have a `local_setting` file, you may want to add the `csw_services` app with these lines:
   
       INSTALLED_APPS += ('csw_services',)

1. To customize the metadata document, use your own service template:  

       CATALOG_SERVICE_METADATA_TEMPLATE = 'xml/service-template.xml'


## Tests

In order to run tests (NOTE: must be in geonode venv), run ``python -m unittest -v``.

## Uninstalling

To uninstall the app:

- remove the service metadata entries from the django admin
- remove the `csw_services` app from the `INSTALLED_APPS`
