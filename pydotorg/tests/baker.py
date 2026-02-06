from model_bakery import baker
from polymorphic.models import PolymorphicModel


class PolymorphicAwareBaker(baker.Baker):
    """
    Our custom model baker ignores the polymorphic_ctype field on all polymorphic
    models - this allows the base class to set it correctly.

    See https://github.com/python/pythondotorg/issues/2567
    """

    def get_fields(self):
        fields = super().get_fields()
        if issubclass(self.model, PolymorphicModel):
            fields = {field for field in fields if field.name != "polymorphic_ctype"}
        return fields
