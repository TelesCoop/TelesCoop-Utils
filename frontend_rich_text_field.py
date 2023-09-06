from enum import Enum

import bleach
from django.db import models


class HTMLTags(Enum):
    A = "a"
    ABBR = "abbr"
    ACRONYM = "acronym"
    B = "b"
    BLOCKQUOTE = "blockquote"
    CODE = "code"
    EM = "em"
    Italic = "i"
    LI = "li"
    OL = "ol"
    STRONG = "strong"
    UL = "ul"
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    H6 = "h6"
    P = "p"


ALLOWED_TAGS = [HTMLTag.value for HTMLTag in HTMLTags]


class FrontendRichTextField(models.TextField):
    """Field that validates text with bleach to prevent XSS attacks."""

    def __init__(self, *args, db_collation=None, **kwargs):
        self.allowed_tags = kwargs.pop("allowed_tags", ALLOWED_TAGS)
        super().__init__(*args, db_collation=db_collation, **kwargs)

    def clean_value(self, value):
        return bleach.clean(value, tags=self.allowed_tags)

    # Update model on save method
    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if value:
            setattr(model_instance, self.attname, self.clean_value(value))
        return value

    # Update db and allow to clean on update method
    def get_prep_value(self, value):
        if value:
            value = self.clean_value(value)
        return super().get_prep_value(value)
