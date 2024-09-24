from datetime import datetime, time
from ConstraintUtilities import select_general, unique_general, prompt_for_date
from Utilities import Utilities
from Department import Department
from Course import Course
from Section import Section
from Student import Student
from Major import Major
from StudentMajor import StudentMajor
from Enrollment import Enrollment
from PassFail import PassFail
from LetterGrade import LetterGrade
from embeded import DepartmentEmbedded, MajorEmbedded, CourseEmbedded
from enums import MinimumSatisfactory
from CommandLogger import CommandLogger, log
from pymongo import monitoring
from Menu import Menu
from Option import Option
from menu_definitions import menu_main, add_select, list_select, delete_select
from pymongo.errors import DuplicateKeyError
from pymongo.errors import WriteError
import io


def check_unique(collection, new_document, column_list) -> bool:
    """
    Validate a document to see whether it duplicates any existing documents already in the collection.
    :param collection:      Reference to the collection that we are about to insert into.
    :param new_document:    The Python dictionary with the data for the new document.
    :param column_list:     The list of columns from the index that we're checking.
    :return:                True if this insert should work wrt to this index, False otherwise.
    """
    find = {}  # initialize the selection criteria.
    # build the search "string" that we'll be searching on.
    # Each element in column_list is a tuple: the column name and whether the column is sorted in ascending
    # or descending order.  I don't care about the direction, just the name of the column.
    for column_name, direction in column_list:
        if column_name in new_document.keys():
            # add the next criteria to the find.  Defaults to a conjunction, which is perfect for this application.
            find[column_name] = new_document[column_name]
    if find:
        # count the number of documents that duplicate this one across the supplied columns.
        return collection.count_documents(find) == 0
    else:
        # All the columns in the index are null in the new document.
        return False


def check_all_unique(collection, new_document):
    """
    Driver for check_unique.  check_unique just looks at one uniqueness constraint for the given collection.
    check_all_unique looks at each uniqueness constraint for the collection by calling check_unique.
    :param collection:
    :param new_document:
    :return:
    """
    # get the index metadata from MongoDB on the sections collection
    collection_ind = collection.index_information()  # Get all the index information
    # Cycle through the indexes one by one.  The variable "index" is just the index name.
    for index in collection_ind:
        if index != '_id_':  # Skip this one since we cannot control it (usually)
            # Get the list of columns in this index.  The index variable is just the name.
            columns = collection_ind[index]
            if columns['unique']:  # make sure this is a uniqueness constraint
                print(
                    f"Unique index: {index} will be respected: {check_unique(Department, new_document, columns['key'])}")


def print_exception(thrown_exception: Exception):
    """
    Analyze the supplied selection and return a text string that captures what violations of the
    schema & any uniqueness constraints that caused the input exception.
    :param thrown_exception:    The exception that MongoDB threw.
    :return:                    The formatted text describing the issue(s) in the exception.
    """
    # Use StringIO as a buffer to accumulate the output.
    with io.StringIO() as output:
        output.write('***************** Start of Exception print *****************\n')
        # DuplicateKeyError is a subtype of WriteError.  So I have to check for DuplicateKeyError first, and then
        # NOT check for WriteError to get this to work properly.
        if isinstance(thrown_exception, DuplicateKeyError):
            error_message = thrown_exception.details
            # There may be multiple columns in the uniqueness constraint.
            # I'm not sure what happens if there are multiple uniqueness constraints violated at the same insert.
            fields = []
            output.write("Uniqueness constraint violated on the fields:")
            # Get the list of fields in the uniqueness constraint.
            for field in iter(error_message['keyValue']):
                fields.append(field)
            output.write(f"{', '.join(fields)}' should be unique.")
        elif isinstance(thrown_exception, WriteError):
            error_message = thrown_exception.details["errInfo"]["details"]
            # In case there are multiple criteria violated at the same time.
            for error in error_message["schemaRulesNotSatisfied"]:
                # One field could have multiple constraints violated.
                field_errors = error.get("propertiesNotSatisfied")
                if field_errors:
                    for field_error in field_errors:
                        field = field_error["propertyName"]
                        reasons = field_error.get("details", [])
                        for reason in reasons:
                            operator_name = reason.get("operatorName")
                            if operator_name == "enum":
                                allowed_values = reason["specifiedAs"]["enum"]
                                output.write(
                                    f"Error: Invalid value for field '{field}'. Allowed values are: {allowed_values}\n")
                            elif operator_name in ["maxLength", "minLength"]:
                                specified_length = reason["specifiedAs"][operator_name]
                                output.write(
                                    f"Error: Invalid length for field '{field}'. The length should be {operator_name} "
                                    f"{specified_length}.\n")
                            elif operator_name == "unique":
                                output.write(
                                    f"Error: field '{field}' already exists. Please choose a different value.\n")
                            elif operator_name == "combineUnique":
                                fields = reason["specifiedAs"]["fields"]
                                output.write(f"Error: Combination of fields '{', '.join(fields)}' should be unique.\n")
                            else:
                                output.write(
                                    f"Error: '{reason['reason']}' for field '{field}'. Please correct the input.\n")
        results = output.getvalue().rstrip()
    return results


def menu_loop(menu: Menu):
    """Little helper routine to just keep cycling in a menu until the user signals that they
    want to exit.
    :param  menu:   The menu that the user will see."""
    action: str = ''
    while action != menu.last_action():
        action = menu.menu_prompt()
        print('next action: ', action)
        exec(action)


def add():
    menu_loop(add_select)


def list():
    menu_loop(list_select)


def delete():
    menu_loop(delete_select)


def select_Department() -> Department:
    return select_general(Department)


def select_Course() -> Course:
    return select_general(Course)


def select_Section() -> Section:
    return select_general(Section)


def select_Major() -> Major:
    return select_general(Major)


def select_Student() -> Student:
    return select_general(Student)


def prompt_for_enum(prompt: str, cls, attribute_name: str):
    """
    MongoEngine attributes can be regulated with an enum.  If they are, the definition of
    that attribute will carry the list of choices allowed by the enum (as well as the enum
    class itself) that we can use to prompt the user for one of the valid values.  This
    represents the 'don't let bad data happen in the first place' strategy rather than
    wait for an exception from the database.
    :param prompt:          A text string telling the user what they are being prompted for.
    :param cls:             The class (not just the name) of the MongoEngine class that the
                            enumerated attribute belongs to.
    :param attribute_name:  The NAME of the attribute that you want a value for.
    :return:                The enum class member that the user selected.
    """
    attr = getattr(cls, attribute_name)  # Get the enumerated attribute.
    if type(attr).__name__ == 'EnumField':  # Make sure that it is an enumeration.
        enum_values = []
        for choice in attr.choices:  # Build a menu option for each of the enum instances.
            enum_values.append(Option(choice.value, choice))
        # Build an "on the fly" menu and prompt the user for which option they want.
        return Menu('Enum Menu', prompt, enum_values).menu_prompt()
    else:
        raise ValueError(f'This attribute is not an enum: {attribute_name}')


def add_department():
    success = False
    new_department = None
    while not success:
        department_name = input('Enter department name (50 character max): ')
        abbreviation = input('Enter abbreviation name (6 character max): ')
        chair_name = input('Enter chair name (80 character max): ')
        building = input('Enter building (ANAC, CDC, DC, ECS, EN2, EN3, EN4, EN5, ET, HSCI, NUR, VEC): ')
        office = int(input('Enter office: '))
        description = input('Enter description (80 character max): ')

        major_embedded = []
        course_embedded = []

        new_department = Department(
            departmentName=department_name,
            abbreviation=abbreviation,
            chairName=chair_name,
            building=building,
            office=office,
            description=description,
            majorEmbedded=major_embedded,
            courseEmbedded=course_embedded
        )

        violated_constraints = unique_general(new_department)
        if violated_constraints:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('Try again')
        else:
            success = True
            try:
                new_department.save()
                print('------------------------------')
                print('Department added successfully!')
                print('------------------------------')
                success = True
            except Exception as e:
                print('Error storing the new department:')
                print(Utilities.print_exception(e))


def add_course():
    success = False
    new_course = None
    while not success:
        abbreviation = input('Enter the department abbreviation (6 character max):')
        course_name = input('Enter course name (50 character max): ')
        course_number = int(input('Enter course number (Range: 100-699): '))
        description = input('Enter description of the course (500 character max): ')
        units = int(input('Enter the units (Range: 1-5): '))

        department = Department.objects(abbreviation=abbreviation).first()
        if not department:
            print('Department with abbreviation', abbreviation, 'not found.')
            continue

        department_name = department.departmentName
        department_abbreviation = department.abbreviation

        department_embedded = DepartmentEmbedded(
            department=department,
            departmentName=department_name,
            abbreviation=department_abbreviation
        )

        new_course = Course(
            abbreviation=abbreviation,
            courseName=course_name,
            courseNumber=course_number,
            description=description,
            units=units,
            departmentEmbedded=department_embedded
        )

        new_course_embedded = CourseEmbedded(
            course=new_course,
            courseNumber=course_number,
            courseName=course_name
        )

        violated_constraints = unique_general(new_course)
        if violated_constraints:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('Try again')
        else:
            success = False
            try:
                new_course.save()
                department.update(push__courseEmbedded=new_course_embedded)
                success = True
                print('------------------------------')
                print('Course added successfully!')
                print('------------------------------')
            except Exception as e:
                print('Errors storing the new course:', e)


def add_section():
    success = False
    new_section = None
    while not success:
        abbreviation = input('Enter department abbreviation: ')
        course_number = input('Enter course number (Range 100-699): ')
        section_number = int(input('Enter section number: '))
        semester = input('Enter semester(Fall, Spring, Summer I, Summer II, Summer III, Winter): ')
        section_year = int(input('Enter section year: '))
        building = input('Enter building (ANAC, CDC, DC, ECS, EN2, EN3, EN4, EN5, ET, HSCI, NUR, VEC): ')
        room_number = int(input('Enter room number (Range 1-999): '))
        schedule = input('Enter schedule (MW, MWF, TuTh, F, S): ')
        start_time_input = input('Enter start time (HH:MM) format between 8:00 and 19:30: ')
        try:
            start_time = datetime.strptime(start_time_input, '%H:%M')
            if not (time(8, 0) <= start_time.time() <= time(19, 30)):
                raise ValueError("Start time must be between 8:00 and 19:30.")
        except ValueError as ve:
            print("Invalid input:", ve)
            continue

        instructor = input('Enter instructor name: ')

        department = Department.objects(abbreviation=abbreviation).first()
        if not department:
            print('Department with abbreviation', abbreviation, 'not found.')
            continue

        course = Course.objects(courseNumber=course_number).first()
        if not course:
            print('Course with number', course_number, 'not found in department', abbreviation)
            continue

        course_embedded = CourseEmbedded(
            course=course,
            courseName=course.courseName,
            courseNumber=course.courseNumber
        )

        new_section = Section(
            courseNumber=course_number,
            sectionNumber=section_number,
            semester=semester,
            sectionYear=section_year,
            building=building,
            roomNumber=room_number,
            schedule=schedule,
            startTime=start_time,
            instructor=instructor,
            course=course_embedded
        )

        violated_constraints = unique_general(new_section)
        if violated_constraints:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('Try again')
        else:
            success = True
            try:
                new_section.save()
                success = False
                print('------------------------------')
                print('Section added successfully!')
                print('------------------------------')
                success = True
            except Exception as e:
                print('Errors storing the new section:')
                print(Utilities.print_exception(e))


def add_major():
    success = False
    new_major = None
    while not success:
        major_name = input('Enter major name: ')
        abbreviation = input('Enter the department abbreviation: ')
        description = input('Enter description (maximum 500): ')

        department = Department.objects(abbreviation=abbreviation).first()
        if not department:
            print('Department with abbreviation', abbreviation, 'not found.')
            continue

        department_name = department.departmentName
        department_abbreviation = department.abbreviation

        department_embedded = DepartmentEmbedded(
            department=department,
            departmentName=department_name,
            abbreviation=department_abbreviation
        )

        new_major = Major(
            majorName=major_name,
            description=description,
            departmentEmbedded=department_embedded
        )

        new_major_embedded = MajorEmbedded(
            major=new_major,
            majorName=major_name
        )

        violated_constraints = unique_general(new_major)
        if violated_constraints:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('Try again')
        else:
            success = False
            try:
                new_major.save()
                department.update(push__majorEmbedded=new_major_embedded)
                print('------------------------------')
                print('Major added successfully!')
                print('------------------------------')
                success = True
            except Exception as e:
                print('Error storing the new major:', e)
                print(Utilities.print_exception(e))


def add_student():
    success = False
    new_student = None
    while not success:
        last_name = input("Enter student's last name: ")
        first_name = input("Enter Student's first name: ")
        e_mail = input('Enter email: ')

        student_major = []
        enrollment = []

        new_student = Student(
            lastName=last_name,
            firstName=first_name,
            eMail=e_mail,
            studentMajor=student_major,
            enrollment=enrollment
        )

        violated_constraints = unique_general(new_student)
        if violated_constraints:
            for violated_constraint in violated_constraints:
                print('Your input values violated constraint: ', violated_constraint)
            print('Try again')
        else:
            success = True
            try:
                new_student.save()
                success = False
                print('------------------------------')
                print('Student added successfully!')
                print('------------------------------')
                success = True

            except Exception as e:
                print('Errors storing the new student:')
                print(Utilities.print_exception(e))


def add_student_major():
    success = False
    new_student_major = None
    while not success:
        student = select_Student()
        major_name = input("Enter major name: ")
        declaration_date = prompt_for_date("Enter declaration date (MM-DD-YYYY): ")

        major = Major.objects(majorName=major_name).first()
        if not major:
            print("major not found.")
            continue

        for student_major in student.studentMajor:
            if student_major.majorName == major_name:
                print('------------------------------')
                print(f'Student is already majored in {student_major.majorName}. Try again.')
                print('------------------------------')
                return
        major_embedded = MajorEmbedded(
            major=major,
            majorName=major_name
        )

        new_student_major = StudentMajor(
            student=student,
            majorName=major_name,
            declarationDate=declaration_date,
            majorEmbedded=[major_embedded]
        )

        try:
            student.studentMajor.append(new_student_major)
            student.save()
            success = False
            print('------------------------------')
            print('Student added to major successfully!')
            print('------------------------------')
            success = True
        except Exception as e:
            print('Errors storing a student to major:')
            print(Utilities.print_exception(e))


def add_enrollment():
    """Enroll a student into a section"""
    success = False
    new_enrollment = None
    while not success:
        student = select_Student()
        abbreviation = input('Enter department abbreviation: ')
        course_number = input('Enter course number: ')
        section_number = input('Enter section number: ')
        semester = input('Enter semester: ')
        section_year = int(input("Enter section year: "))

        department = Department.objects(abbreviation=abbreviation).first()
        if not department:
            print('Department with abbreviation', abbreviation, 'not found.')
            continue

        section = Section.objects(sectionNumber=section_number).first()
        if not section:
            print('------------------------------')
            print('Section not found.')
            print('------------------------------')
            continue

        for enrollment in student.enrollment:
            if enrollment.course_number == course_number:
                print('------------------------------')
                print('Student is already enrolled in the same course. Try again.')
                print('------------------------------')
                break
        else:
            section = Section.objects(sectionNumber=section_number, courseNumber=course_number).first()
            if not section:
                print('------------------------------')
                print('The specified section does not belong to the selected course. Try again.')
                print('------------------------------')
                continue

            pass_fail_choice = input('Enter pass/fail (P) or letter grade (L): ').upper()
            if pass_fail_choice not in ['P', 'L']:
                print('------------------------------')
                print('Invalid. Please enter P for pass/fail or L for letter grade.')
                print('------------------------------')
                continue

            if pass_fail_choice == 'P':
                application_date = prompt_for_date('Enter application date: ')

                pass_fail = PassFail(
                    sectionNumber=section_number,
                    applicationDate=application_date
                )
                letter_grade = None

            else:
                min_satisfactory = input('Enter minimum satisfactory grade: ')
                if not any(min_satisfactory == ms.value for ms in MinimumSatisfactory):
                    print('------------------------------')
                    print('Invalid choice for minimum satisfactory grade.')
                    print('------------------------------')
                    continue

                letter_grade = LetterGrade(
                    sectionNumber=section_number,
                    min_satisfactory=min_satisfactory
                )
                pass_fail = None

            new_enrollment = Enrollment(
                student=student,
                abbreviation=abbreviation,
                courseNumber=course_number,
                sectionNumber=section_number,
                semester=semester,
                sectionYear=section_year,
                passFail=pass_fail,
                letterGrade=letter_grade
            )

            try:
                student.enrollment.append(new_enrollment)
                student.save()

                print('------------------------------')
                print('Student has been enrolled successfully!')
                print('------------------------------')
                success = True
            except Exception as e:
                print('Error enrolling student:')
                print(e)


def list_department():
    departments = Department.objects()
    for department in departments:
        print("------------------------------------------------ ")
        print(department)
        print("------------------------------------------------ ")


def list_course():
    courses = Course.objects()
    for course in courses:
        print("--------List of courses in Department-----------")
        print(course)
        print("------------------------------------------------")


def list_section():
    courses = Course.objects()
    for course in courses:
        sections = Section.objects(courseNumber=course.courseNumber)
        for section in sections:
            print(f"\n----- List of Sections in the selected Course -------")
            print(section)
            print("------------------------------------------------------")


def list_major():
    majors = Major.objects()
    for major in majors:
        print("----------------List of majors in Department------------")
        print(major)
        print("--------------------------------------------------------")


def list_student():
    students = Student.objects()
    print("---------List of students---------------------------------")
    for student in students:
        print(student)
    print("--------------------------------------------------------")

def list_student_major():
    last_name = input('Enter students last name: ')
    first_name = input('Enter students first name: ')
    student = Student.objects(lastName=last_name, firstName=first_name).first()
    if not student:
        print('-------------------------------')
        print("student not found")
        print('-------------------------------')
        return

    print(f"\n----- List of majors of a selected student --------- \n"
          f"Student: {student.firstName} {student.lastName}")

    student_majors = student.studentMajor

    if student_majors:
        for student_major in student_majors:
            print(student_major)
    else:
        print("Student is not enrolled in any majors.")
        print("------------------------------------------------- ")
    print("------------------------------------------------- ")


def list_enrollment():
    last_name = input('Enter student\'s last name: ')
    first_name = input('Enter student\'s first name: ')

    student = Student.objects(lastName=last_name, firstName=first_name).first()
    if not student:
        print('-------------------------------')
        print("Student not found")
        print('-------------------------------')
        return

    print(f"\n----- List of enrollments of a student ----------- \n"
          f"{student.firstName} {student.lastName} is enrolled in: ")

    enrollments = student.enrollment

    if enrollments:
        for enrollment in enrollments:
            print(enrollment)
    else:
        print("Student is not enrolled in any course/section.")
        print("------------------------------------------------ ")
    print("------------------------------------------------ ")


def delete_department():
    department_abbreviation = input("Enter the abbreviation of the department to delete: ")
    department = Department.objects(abbreviation=department_abbreviation).first()
    if not department:
        print("Department not found.")
        return
    courses_in_department = Course.objects(abbreviation=department_abbreviation)
    if courses_in_department:
        print("This department cannot be deleted since courses are found in this department.")
        return
    department.delete()
    print('--------------------------------')
    print("Department deleted successfully.")
    print('--------------------------------')


def delete_course():
    department_abbreviation = input("Enter the department abbreviation: ")
    department = Department.objects(abbreviation=department_abbreviation).first()
    if not department:
        print("Department not found.")
        return

    course_number = input("Enter the course number to delete: ")
    course = Course.objects(courseNumber=course_number).first()
    if not course:
        print("Course not found.")
        return

    sections_with_course = Section.objects(courseNumber=course_number)
    if sections_with_course:
        print("This course cannot be deleted since sections are found in this course.")
        return

    course.delete()
    print('------------------------------')
    print(" Course deleted successfully.")
    print('------------------------------')


def delete_section():
    department_abbreviation = input("Enter the department abbreviation: ")
    department = Department.objects(abbreviation=department_abbreviation).first()
    if not department:
        print("Department not found.")
        return

    course_number = input("Enter the course number: ")
    course = Course.objects(courseNumber=course_number).first()
    if not course:
        print('-------------------------------')
        print("Course not found.")
        print('-------------------------------')
        return

    section_number = input("Enter the section number to delete: ")
    section = Section.objects(sectionNumber=section_number).first()
    if not section:
        print('-------------------------------')
        print("Section not found.")
        print('-------------------------------')
        return

    if Student.objects(enrollment__sectionNumber=section_number).first():
        print("This section cannot be deleted since a student is enrolled in this section.")
        return

    section.delete()
    print('-------------------------------')
    print(" Section deleted successfully.")
    print('------------------------------')


def delete_major():
    major_name = input("Enter the name of the major to delete: ")

    major = Major.objects(majorName=major_name).first()
    if not major:
        print('-------------------------------')
        print("Major not found.")
        print('-------------------------------')
        return

    students = Student.objects()

    for student in students:
        for student_major in student.studentMajor:
            if student_major.majorName == major_name:
                print("This major cannot be deleted since a student is declared in this major.")
                return

    major.delete()
    print('-------------------------------')
    print(" Major deleted successfully.")
    print('-------------------------------')


def delete_student():
    last_name = input("Enter student\'s last name: ")
    first_name = input("Enter student\'s first name: ")

    student = Student.objects(lastName=last_name, firstName=first_name).first()
    if not student:
        print('-------------------------------')
        print("Student not found.")
        print('-------------------------------')
        return

    for enrollment in student.enrollment:
        if enrollment.student == student:
            print("This student cannot be deleted since a student is enrolled in sections.")
            return

    for student_major in student.studentMajor:
        if student_major.student == student:
            print("This student cannot be deleted since a student is declared in a major.")
            return

    student.delete()
    print('-------------------------------')
    print(" Student deleted successfully.")
    print('-------------------------------')


def delete_student_major():
    last_name = input("Enter student\'s last name: ")
    first_name = input("Enter student\'s first name: ")
    student = Student.objects(lastName=last_name, firstName=first_name).first()
    if not student:
        print('-------------------------------')
        print("Student not found.")
        print('-------------------------------')
        return

    major_name = input(f"Enter the major name to delete from student: ")
    major_associated = False
    for major in student.studentMajor:
        if major.majorName == major_name:
            major_associated = True
            break

    if not major_associated:
        print('-------------------------------')
        print("Major specified is not associated with the student.")
        print('-------------------------------')
        return

    major = Major.objects(majorName=major_name).first()
    if not major:
        print('-------------------------------')
        print("Major not found.")
        print('-------------------------------')
        return

    student_major_to_delete = None
    for student_major in student.studentMajor:
        if str(student_major.majorName).strip() == str(major_name).strip():
            student_major_to_delete = student_major
            break

    if not student_major_to_delete:
        print('-------------------------------')
        print("Major not found from student.")
        print('-------------------------------')
        return

    student.update(pull__studentMajor=student_major_to_delete)
    print('-----------------------------------------------')
    print(f"Major is deleted from the student successfully.")
    print('-----------------------------------------------')


def delete_enrollment():
    last_name = input("Enter student\'s last name: ")
    first_name = input("Enter student\'s first name: ")
    student = Student.objects(lastName=last_name, firstName=first_name).first()
    if not student:
        print('-------------------------------')
        print("Student not found.")
        print('-------------------------------')
        return

    department_abbreviation = input("Enter the department abbreviation: ")
    department = Department.objects(abbreviation=department_abbreviation).first()
    if not department:
        print("Department not found.")
        return

    course_number = input("Enter the course number: ")
    course = Course.objects(courseNumber=course_number).first()
    if not course:
        print('-------------------------------')
        print("Course not found.")
        print('-------------------------------')
        return

    section_number = input("Enter the section number to delete: ")

    section = Section.objects(sectionNumber=section_number).first()
    if not section:
        print('-------------------------------')
        print("Section not found.")
        print('-------------------------------')
        return

    enrollment_to_delete = None
    for enrollment in student.enrollment:
        if str(enrollment.sectionNumber).strip() == str(section_number).strip():
            enrollment_to_delete = enrollment
            break

    if not enrollment_to_delete:
        print('-------------------------------')
        print("Enrollment not found.")
        print('-------------------------------')
        return

    student.update(pull__enrollment=enrollment_to_delete)
    print('------------------------------')
    print(f"Enrollment is deleted from Student successfully.")
    print('------------------------------')


if __name__ == '__main__':
    print('Starting in main.')
    monitoring.register(CommandLogger())
    db = Utilities.startup()
    main_action: str = ''
    while main_action != menu_main.last_action():
        main_action = menu_main.menu_prompt()
        print('next action: ', main_action)
        exec(main_action)
    log.info('All done for now.')
