from django.conf import settings
from drf_spectacular.settings import SpectacularSettings, SPECTACULAR_DEFAULTS, IMPORT_STRINGS
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView
from rest_framework.response import Response

spectacular_settings = SpectacularSettings(
    user_settings=getattr(settings, 'SPECTACULAR_SETTINGS_ADMIN', {}),
    defaults=SPECTACULAR_DEFAULTS,
    import_strings=IMPORT_STRINGS,)



class AdminSpectacularAPIView(SpectacularAPIView):
    permission_classes = spectacular_settings.SERVE_PERMISSIONS
    generator_class = spectacular_settings.DEFAULT_GENERATOR_CLASS
    serve_public = spectacular_settings.SERVE_PUBLIC
    urlconf = spectacular_settings.SERVE_URLCONF

    def _get_filename(self, request, version):
        return "{title}{version}.{suffix}".format(
            title=spectacular_settings.TITLE or 'schema',
            version=f' ({version})' if version else '',
            suffix=self.perform_content_negotiation(request, force=True)[0].format
        )

    def _get_schema_response(self, request):
        # version specified as parameter to the view always takes precedence. after
        # that we try to source version through the schema view's own versioning_class.
        version = self.api_version or request.version or self._get_version_parameter(request)
        generator = self.generator_class(urlconf=self.urlconf, api_version=version, patterns=self.patterns, spectacular_settings=spectacular_settings)
        return Response(
            data=generator.get_schema(request=request, public=self.serve_public),
            headers={"Content-Disposition": f'inline; filename="{self._get_filename(request, version)}"'}
        )


class AdminSpectacularSwaggerView(SpectacularSwaggerView):
    url_name = "admin_schema"

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        return Response(
            data={
                'title': self.title,
                'swagger_ui_css': self._swagger_ui_resource('swagger-ui.css'),
                'swagger_ui_bundle': self._swagger_ui_resource('swagger-ui-bundle.js'),
                'swagger_ui_standalone': self._swagger_ui_resource('swagger-ui-standalone-preset.js'),
                'favicon_href': self._swagger_ui_favicon(),
                'schema_url': self._get_schema_url(request),
                'settings': self._dump(spectacular_settings.SWAGGER_UI_SETTINGS),
                'oauth2_config': self._dump(spectacular_settings.SWAGGER_UI_OAUTH2_CONFIG),
                'template_name_js': self.template_name_js,
                'csrf_header_name': self._get_csrf_header_name(),
                'schema_auth_names': self._dump(self._get_schema_auth_names()),
            },
            template_name=self.template_name,
        )
