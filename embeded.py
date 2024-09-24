from mongoengine import *


class DepartmentEmbedded(EmbeddedDocument):
    department = ReferenceField('Department', db_field='department', required=True)

    departmentName = StringField(db_field='department_name', max_length=50)
    abbreviation = StringField(db_field='abbreviation', min_length=1, max_length=6, required=True)

    def __str__(self):
        return (f'department name: {self.departmentName}\n'
                f'department abbreviation: {self.abbreviation}')


class MajorEmbedded(EmbeddedDocument):
    major = ReferenceField('Major', db_field='major', required=True)

    majorName = StringField(db_field='major_name', min_length=3, max_length=80, required=True)

    def __str__(self):
        return f'major name: {self.majorName}'


class CourseEmbedded(EmbeddedDocument):
    course = ReferenceField('Course', db_field='course', required=True)
    courseNumber = IntField(db_field='course_number', min_value=100, max_value=699, required=True)
    courseName = StringField(db_field='course_name', max_length=50, required=True)

    def __str__(self):
        return (f'course name: {self.courseName}\n')
