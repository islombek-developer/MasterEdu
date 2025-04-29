from django.conf import settings
from drf_spectacular.openapi import AutoSchema

from drf_spectacular.utils import OpenApiParameter


class CustomAutoSchema(AutoSchema):
    global_params = [
        OpenApiParameter(
            name="Accept-Language",
            type=str,
            enum=[lang[0] for lang in settings.LANGUAGES],
            location=OpenApiParameter.HEADER,
            description="`uz`,`en`, `ru`. The default value is `uz`",
        )
    ]

    def get_override_parameters(self):
        params = super().get_override_parameters()
        return params + self.global_params
