from mongoengine import *
from enums import MinimumSatisfactory


class LetterGrade(EmbeddedDocument):
    sectionNumber = IntField(db_field='section_number', required=True)
    min_satisfactory = EnumField(MinimumSatisfactory, required=True)


    def __str__(self):
        return (f"Section Number: {self.sectionNumber}\n"
                f"Minimum satisfactory: {self.min_satisfactory}")
