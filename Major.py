from mongoengine import *
from embeded import DepartmentEmbedded


class Major(Document):
    majorName = StringField(db_field='major_name', min_length=3, max_length=80, required=True)
    description = StringField(db_field='description', max_length=500, required=True)

    departmentEmbedded = EmbeddedDocumentField('DepartmentEmbedded', db_field='department_embedded', required=True)

    meta = {
        'collection': 'majors',
        'indexes': [
            {'unique': True, 'fields': ['majorName'], 'name': 'major_uk_01'}
        ]
    }


    def __str__(self):
        return (f'Department: {self.departmentEmbedded.departmentName}\n'
                f'  major name: {self.majorName}\n'
                f'  Description: {self.description}')
