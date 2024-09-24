from mongoengine import *
from PassFail import PassFail
from LetterGrade import LetterGrade
from enums import Semester


class Enrollment(EmbeddedDocument):
    student = ReferenceField("Student", db_field='student', required=True)
    abbreviation = StringField(db_field='abbreviation',min_length=1, max_length=6, required=True)
    courseNumber = IntField(db_field='course_number', min_value=100, max_value=699, required=True)
    sectionNumber = IntField(db_field='section_number', required=True)
    semester = EnumField(Semester, required=True)
    sectionYear = IntField(db_field='section_year', required=True)

    passFail = EmbeddedDocumentField('PassFail', db_field='pass_fail')
    letterGrade = EmbeddedDocumentField('LetterGrade', db_field='letter_grade')

    meta = {
        'collection': 'enrollments',
        'indexes': [
            {'unique': True, 'fields': ['student', 'section_number'], 'name': 'enrollment_uk_01'},
            {'unique': True,
             'fields': ['semester', 'sectionYear', 'abbreviation', 'courseNumber', 'studentID'],
             'name': 'enrollment_uk_02'}
        ]
    }

    def __str__(self):
        return (f"    - Course number: {self.courseNumber}\n"
                f"    - Section: {self.sectionNumber}\n"
                f"    - Semester: {self.semester.value}\n"
                f"    - Section year: {self.sectionYear}\n")
