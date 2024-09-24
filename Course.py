from mongoengine import *
from embeded import DepartmentEmbedded

class Course(Document):
    courseName = StringField(db_field='course_name', max_length=50, required=True)
    courseNumber = IntField(db_field='course_number', min_value=100, max_value=699, required=True)
    description = StringField(db_field='description', max_length=500, required=True)
    units = IntField(db_field='units', min_value=1, max_value=5, required=True)
    abbreviation = StringField(db_field='abbreviation', min_length=1, max_length=6, required=True)

    departmentEmbedded = EmbeddedDocumentField(DepartmentEmbedded, db_field='department_embedded', required=True)

    meta = {
        'collection': 'courses',
        'indexes': [
            {'unique': True, 'fields': ['abbreviation', 'courseNumber'], 'name': 'course_uk_01'},
            {'unique': True, 'fields': ['abbreviation', 'courseName'], 'name': 'course_uk_02'}
        ]
    }


    def __str__(self):
        results = (f"Department: {self.departmentEmbedded.departmentName}\n"
                   f"    Course Name: {self.courseName}\n"
                   f"    Course Number: {self.courseNumber}\n"
                   f'    Units: {self.units}\n'
                   f"    Description: {self.description}")
        return results


