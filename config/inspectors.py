from drf_yasg.inspectors import SwaggerAutoSchema

class CustomAutoSchema(SwaggerAutoSchema):
    def get_view_serializer(self):
        if getattr(self.view, 'swagger_fake_view', False):
            return None
        return super().get_view_serializer()

    def get_query_serializer(self):
        if getattr(self.view, 'swagger_fake_view', False):
            return None
        return super().get_query_serializer()