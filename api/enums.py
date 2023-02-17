import enum


class APIEnum(enum.Enum):
    @classmethod
    def choices(cls):
        return [(key.name, key.value) for key in cls]

    @classmethod
    def get_name(cls, value):
        for key in cls:
            if key.value == value:
                return key.name

    @classmethod
    def get_value(cls, name):
        for key in cls:
            if key.name == name:
                return key.value


class SocialAppProviders(APIEnum):
    Google = 'Google Plus'
    FB = 'Facebook'
    AF = 'Atalanta Fit'

    # @classmethod
    # def as_choices(cls):
    #     return [(key.name, key.value) for key in cls]
