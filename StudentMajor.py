from mongoengine import *
from datetime import datetime
from embeded import MajorEmbedded


class StudentMajor(EmbeddedDocument):
    student = ReferenceField('Student', db_field='student', required=True)
    majorName = StringField(db_field='major_name', required=True)
    declarationDate = DateField(db_field='declaration_date', required=True)

    majorEmbedded = ListField(EmbeddedDocumentField('MajorEmbedded', db_field='major_embedded', required=True))

    meta = {
        'collection': 'studentMajors',
        'indexes': [
            {'unique': True, 'fields': ['student', 'majorName'], 'name': 'student_major_uk_01'}
        ]
    }

    def __str__(self):
        return (f'  Major: {self.majorName}\n'
                f'      Declared date: {self.declarationDate}\n')
