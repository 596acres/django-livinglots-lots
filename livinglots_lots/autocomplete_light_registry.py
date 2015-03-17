from autocomplete_light import (AutocompleteGenericBase, AutocompleteModelBase,
                                register)

from livinglots import get_lot_model, get_lotgroup_model


class LotAutocomplete(AutocompleteModelBase):
    autocomplete_js_attributes = {'placeholder': 'lot name',}
    search_fields = ('bbl', 'name',)

    def choices_for_request(self):
        choices = super(LotAutocomplete, self).choices_for_request()
        if not self.request.user.is_staff:
            choices = choices.none()
        return choices


class LotGroupAutocomplete(AutocompleteModelBase):
    autocomplete_js_attributes = {'placeholder': 'lot group name',}
    search_fields = ('name',)

    def choices_for_request(self):
        choices = super(LotGroupAutocomplete, self).choices_for_request()
        if not self.request.user.is_staff:
            choices = choices.none()
        return choices


class AutocompleteOrganizableItems(AutocompleteGenericBase):
    choices = (
        get_lot_model().objects.all(),
    )

    search_fields = (
        ('bbl', 'name',),
    )


register(AutocompleteOrganizableItems)
register(get_lot_model(), LotAutocomplete)
register(get_lotgroup_model(), LotGroupAutocomplete)
