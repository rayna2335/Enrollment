from mongoengine import *
from enums import Building
from embeded import MajorEmbedded


class Department(Document):
    departmentName = StringField(db_field='department_name', max_length=50, required=True)
    abbreviation = StringField(db_field='abbreviation',min_length=1, max_length=6, required=True)
    chairName = StringField(db_field='chair_name', min_length=3, max_length=80, required=True)
    building = EnumField(Building, required=True)
    office = IntField(db_field='office', required=True)
    description = StringField(db_field='description', max_length=80, required=True)

    majorEmbedded = ListField(EmbeddedDocumentField('MajorEmbedded', db_field='major_embedded', required=True))
    courseEmbedded = ListField(EmbeddedDocumentField('CourseEmbedded', db_field='course_embedded', required=True))

    meta = {
        'collection': 'departments',
        'indexes': [
            {'unique': True, 'fields': ['abbreviation'], 'name': 'department_uk_01'},
            {'unique': True, 'fields': ['departmentName'], 'name': 'department_uk_02'},
            {'unique': True, 'fields': ['chairName'], 'name': 'department_uk_03'},
            {'unique': True, 'fields': ['building', 'office'], 'name': 'department_uk_04'},
        ]
    }

    def __str__(self):
        results = (f'Department name: {self.departmentName}\n'
                   f'   Abbreviation: {self.abbreviation}\n'
                   f'   Chair name: {self.chairName}\n'
                   f'   Building: {self.building.value}\n'
                   f'   Office: {self.office}\n'
                   f'   Description: {self.description}')
        return results

