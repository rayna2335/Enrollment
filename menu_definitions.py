from Menu import Menu
import logging
from Option import Option

menu_logging = Menu('debug', 'Please select the logging level from the following:', [
    Option("Debugging", "logging.DEBUG"),
    Option("Informational", "logging.INFO"),
    Option("Error", "logging.ERROR")
])

# The main options for operating on Departments and Courses.
menu_main = Menu('main', 'Please select one of the following options:', [
    Option("Add", "add()"),
    Option("List", "list()"),
    Option("Delete", "delete()"),
    Option("Exit this application", "pass")
])

add_select = Menu('add', 'Please indicate what you want to add:', [
    Option("Add Department", "add_department()"),
    Option("Add Course", "add_course()"),
    Option("Add Section", "add_section()"),
    Option("Add Major", "add_major()"),
    Option("Add Student", "add_student()"),
    Option("Add Student to Major", "add_student_major()"),
    Option("Add Enrollment Student to Section", "add_enrollment()"),
    Option("Exit", "pass")
])

list_select = Menu('list', 'Please indicate what you want to list:', [
    Option("List all Department", "list_department()"),
    Option("List all Course", "list_course()"),
    Option("List all section", "list_section()"),
    Option("List all Major", "list_major()"),
    Option("List all Student", "list_student()"),
    Option("List all Student to Major", "list_student_major()"),
    Option("List all Enrollment by Student", "list_enrollment()"),
    Option("Exit", "pass")
])


delete_select = Menu('delete', 'Please indicate what you want to delete from:', [
    Option("Delete Department", "delete_department()"),
    Option("Delete Course", "delete_course()"),
    Option("Delete section", "delete_section()"),
    Option("Delete Major", "delete_major()"),
    Option("Delete Student", "delete_student()"),
    Option("Delete Student to Major", "delete_student_major()"),
    Option("Delete Enrollment by Student", "delete_enrollment()"),
    Option("Exit", "pass")
])

