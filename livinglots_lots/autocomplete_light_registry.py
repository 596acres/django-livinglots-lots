from autocomplete_light import AutocompleteModelBase, register

from livinglots import get_lotgroup_model


class LotGroupAutocomplete(AutocompleteModelBase):
    autocomplete_js_attributes = {'placeholder': 'lot group name',}
    search_fields = ('name',)

    def choices_for_request(self):
        choices = super(LotGroupAutocomplete, self).choices_for_request()
        if not self.request.user.is_staff:
            choices = choices.none()
        return choices


register(get_lotgroup_model(), LotGroupAutocomplete)
