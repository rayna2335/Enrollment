from mongoengine import *
from Enrollment import Enrollment
from StudentMajor import StudentMajor

class Student(Document):
    lastName = StringField(db_field='last_name', required=True)
    firstName = StringField(db_field='first_name', required=True)
    eMail = StringField(db_field='e_mail', required=True)

    studentMajor = ListField(EmbeddedDocumentField('StudentMajor', db_field='student_major', required=True))
    enrollment = ListField(EmbeddedDocumentField('Enrollment', db_field='enrollment', required=True))


    meta = {
        'collection': 'students',
        'indexes': [
            {'unique': True, 'fields': ['lastName', 'firstName'], 'name': 'student_uk_01'},
            {'unique': True, 'fields': ['eMail'], 'name': 'student_uk_02'}
        ]
    }




    def __str__(self):
        results = (f"Student's last name: {self.lastName}\n"
                   f"Student's first name: {self.firstName}\n"
                   f"email: {self.eMail}")

        return results
