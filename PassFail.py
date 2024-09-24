from mongoengine import *


class PassFail(EmbeddedDocument):
    sectionNumber = IntField(db_field='section_number', required=True)
    applicationDate = DateTimeField(db_field='application_date', required=True)

    def __str__(self):
        return (f"Section Number: {self.sectionNumber}\n"
                f"Application Date: {self.applicationDate}")
