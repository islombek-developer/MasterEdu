import os
import re

from drf_spectacular.drainage import get_override, warn, error, reset_generator_stats, add_trace_message
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import is_versioning_supported, camelize_operation, build_root_object, \
    sanitize_result_object, normalize_result_object, operation_matches_version, modify_for_versioning
from drf_spectacular.settings import spectacular_settings



class CustomSchemaGenerator(SchemaGenerator):

    def __init__(self, *args, **kwargs):
        self.spectacular_settings = kwargs.pop('spectacular_settings', spectacular_settings)
        super().__init__(*args, **kwargs)

    def coerce_path(self, path, method, view):
        """
        Customized coerce_path which also considers the `_pk` suffix in URL paths
        of nested routers.
        """
        path = super().coerce_path(path, method, view)  # take care of {pk}
        if self.spectacular_settings.SCHEMA_COERCE_PATH_PK_SUFFIX:
            path = re.sub(pattern=r'{(\w+)_pk}', repl=r'{\1_id}', string=path)
        return path

    def parse(self, input_request, public):
        """ Iterate endpoints generating per method path operations. """
        result = {}
        self._initialise_endpoints()
        endpoints = self._get_paths_and_endpoints()

        if self.spectacular_settings.SCHEMA_PATH_PREFIX is None:
            # estimate common path prefix if none was given. only use it if we encountered more
            # than one view to prevent emission of erroneous and unnecessary fallback names.
            non_trivial_prefix = len(set([view.__class__ for _, _, _, view in endpoints])) > 1
            if non_trivial_prefix:
                path_prefix = os.path.commonpath([path for path, _, _, _ in endpoints])
                path_prefix = re.escape(path_prefix)  # guard for RE special chars in path
            else:
                path_prefix = '/'
        else:
            path_prefix = self.spectacular_settings.SCHEMA_PATH_PREFIX
        if not path_prefix.startswith('^'):
            path_prefix = '^' + path_prefix  # make sure regex only matches from the start

        for path, path_regex, method, view in endpoints:
            # emit queued up warnings/error that happened prior to generation (decoration)
            for w in get_override(view, 'warnings', []):
                warn(w)
            for e in get_override(view, 'errors', []):
                error(e)

            view.request = self.spectacular_settings.GET_MOCK_REQUEST(method, path, view, input_request)

            if not (public or self.has_view_permissions(path, method, view)):
                continue

            if view.versioning_class and not is_versioning_supported(view.versioning_class):
                warn(
                    f'using unsupported versioning class "{view.versioning_class}". view will be '
                    f'processed as unversioned view.'
                )
            elif view.versioning_class:
                version = (
                        self.api_version  # explicit version from CLI, SpecView or SpecView request
                        or view.versioning_class.default_version  # fallback
                )
                if not version:
                    continue
                path = modify_for_versioning(self.inspector.patterns, method, path, view, version)
                if not operation_matches_version(view, version):
                    continue

            assert isinstance(view.schema, AutoSchema), (
                f'Incompatible AutoSchema used on View {view.__class__}. Is DRF\'s '
                f'DEFAULT_SCHEMA_CLASS pointing to "drf_spectacular.openapi.AutoSchema" '
                f'or any other drf-spectacular compatible AutoSchema?'
            )
            with add_trace_message(getattr(view, '__class__', view)):
                operation = view.schema.get_operation(
                    path, path_regex, path_prefix, method, self.registry
                )

            # operation was manually removed via @extend_schema
            if not operation:
                continue

            if self.spectacular_settings.SCHEMA_PATH_PREFIX_TRIM:
                path = re.sub(pattern=path_prefix, repl='', string=path, flags=re.IGNORECASE)

            if self.spectacular_settings.SCHEMA_PATH_PREFIX_INSERT:
                path = self.spectacular_settings.SCHEMA_PATH_PREFIX_INSERT + path

            if not path.startswith('/'):
                path = '/' + path

            if self.spectacular_settings.CAMELIZE_NAMES:
                path, operation = camelize_operation(path, operation)

            result.setdefault(path, {})
            result[path][method.lower()] = operation

        return result
    def get_schema(self, request=None, public=False):
        """ Generate a OpenAPI schema. """
        reset_generator_stats()
        result = build_root_object(
            paths=self.parse(request, public),
            components=self.registry.build(self.spectacular_settings.APPEND_COMPONENTS),
            version=self.api_version or getattr(request, 'version', None),
            webhooks={}  # Add this line
        )
        for hook in self.spectacular_settings.POSTPROCESSING_HOOKS:
            result = hook(result=result, generator=self, request=request, public=public)

        return sanitize_result_object(normalize_result_object(result))

