from datetime import datetime, time
from enums import Schedule, Semester, Building
from mongoengine import *
from embeded import CourseEmbedded

class Section(Document):
    courseNumber = IntField(db_field='course_number', min_value=100, max_value=699, required=True)
    sectionNumber = IntField(db_field='section_number', required=True)
    semester = EnumField(Semester, required=True)
    sectionYear = IntField(db_field='section_year', required=True)
    building = EnumField(Building, required=True)
    roomNumber = IntField(db_field='room', min_value=1, max_value=999, required=True)
    schedule = EnumField(Schedule, required=True)
    startTime = DateTimeField(db_field='startTime', required=True)
    instructor = StringField(db_field='instructor', required=True)

    course = EmbeddedDocumentField('CourseEmbedded', db_field='course_embedded', required=True)

    meta = {
        'collection': 'sections',
        'indexes': [
            {'unique': True, 'fields': ['course', 'sectionNumber', 'semester', 'sectionYear'], 'name': 'section_uk_01'},
            {'unique': True, 'fields': ['semester', 'sectionYear', 'building', 'roomNumber', 'schedule', 'startTime'],
             'name': 'section_uk_02'},
            {'unique': True, 'fields': ['semester', 'sectionYear', 'schedule', 'startTime', 'instructor'],
             'name': 'section_uk_03'}
        ]
    }

    def __str__(self):
        results = (f'Course: {self.course.courseName} {self.course.courseNumber}\n'
                   f'   Section Number: {self.sectionNumber}\n'
                   f'   Semester: {self.semester}\n'
                   f'   Section Year: {self.sectionYear}\n'
                   f'   Building: {self.building}\n'
                   f'   Room Number: {self.roomNumber}\n'
                   f'   Schedule: {self.schedule}\n'
                   f'   StartTime: {self.startTime}\n'
                   f'   Instructor: {self.instructor}')
        return results
