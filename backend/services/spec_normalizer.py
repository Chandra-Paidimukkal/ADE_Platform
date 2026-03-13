from config.spec_dictionary import SPEC_DICTIONARY


def normalize_field(field):

    field = field.lower()

    for standard, aliases in SPEC_DICTIONARY.items():

        if field == standard:
            return standard

        if field in aliases:
            return standard

    return field