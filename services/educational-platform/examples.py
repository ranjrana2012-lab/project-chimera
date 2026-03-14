"""Example Curriculum and Data for Educational Platform.

This module provides example courses, lessons, and assessments
demonstrating the platform's capabilities.
"""

from datetime import datetime
from models import (
    Course, Lesson, Assessment, EducatorProfile,
    LearningObjective, Skill, DifficultyLevel,
    ContentType, AssessmentType
)


# Example Educator
EXAMPLE_EDUCATOR = EducatorProfile(
    name="Dr. Sarah Chen",
    email="sarah.chen@bmet.ac.uk",
    institution="BMet College",
    department="Digital Technologies",
    subjects=["Computer Science", "Mathematics"],
    areas_of_expertise=["Programming", "Data Science", "AI/ML"],
    qualifications=["PhD Computer Science", "PGCE"],
    years_of_experience=15,
    can_create_courses=True,
    can_view_analytics=True
)


# Example Skills
PROGRAMMING_SKILLS = [
    Skill(
        name="Python Basics",
        category="programming",
        description="Fundamental Python programming concepts",
        difficulty_level=DifficultyLevel.BEGINNER,
        estimated_learning_hours=2.0,
        learning_objectives=[
            LearningObjective(
                title="Write Simple Programs",
                description="Create basic Python scripts",
                blooms_taxonomy_level="apply"
            ),
            LearningObjective(
                title="Use Variables",
                description="Understand and use variables in Python",
                blooms_taxonomy_level="remember"
            )
        ]
    ),
    Skill(
        name="Data Types",
        category="programming",
        description="Understanding Python data types",
        difficulty_level=DifficultyLevel.BEGINNER,
        estimated_learning_hours=1.5,
        prerequisites=["Python Basics"],
        learning_objectives=[
            LearningObjective(
                title="Identify Data Types",
                description="Recognize different data types",
                blooms_taxonomy_level="understand"
            ),
            LearningObjective(
                title="Convert Types",
                description="Convert between data types",
                blooms_taxonomy_level="apply"
            )
        ]
    ),
    Skill(
        name="Control Flow",
        category="programming",
        description="If statements and loops in Python",
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        estimated_learning_hours=3.0,
        prerequisites=["Python Basics", "Data Types"],
        learning_objectives=[
            LearningObjective(
                title="Write Conditional Logic",
                description="Use if/elif/else statements",
                blooms_taxonomy_level="apply"
            ),
            LearningObjective(
                title="Implement Loops",
                description="Use for and while loops",
                blooms_taxonomy_level="apply"
            )
        ]
    )
]


# Example Course: Introduction to Python
INTRO_TO_PYTHON_COURSE = Course(
    title="Introduction to Python Programming",
    description="Learn the fundamentals of Python programming with hands-on exercises",
    subject="Computer Science",
    grade_level="Year 10",
    educator_id=EXAMPLE_EDUCATOR.id,
    educator_name=EXAMPLE_EDUCATOR.name,
    department=EXAMPLE_EDUCATOR.department,
    difficulty_level=DifficultyLevel.BEGINNER,
    estimated_duration_hours=10.0,
    tags=["programming", "python", "beginner"],
    learning_objectives=[
        LearningObjective(
            title="Write Python Programs",
            description="Create working Python programs",
            blooms_taxonomy_level="create"
        ),
        LearningObjective(
            title="Debug Code",
            description="Find and fix errors in code",
            blooms_taxonomy_level="analyze"
        )
    ],
    skills_taught=[skill.id for skill in PROGRAMMING_SKILLS],
    lessons=[
        Lesson(
            title="Welcome to Python",
            description="Introduction to Python programming",
            order=1,
            content_type=ContentType.TEXT,
            text_content="""
# Welcome to Python Programming!

Python is a powerful, easy-to-learn programming language.
In this course, you'll learn the fundamentals of programming.

## What You'll Learn
- Variables and data types
- Control flow (if statements, loops)
- Functions and modules
- Basic problem solving

## Let's Get Started!
Your first Python program:
```python
print("Hello, World!")
```
            """.strip(),
            duration_minutes=15,
            bsl_available=True,
            captions_available=True,
            audio_description_available=False,
            difficulty_level=DifficultyLevel.BEGINNER,
            tags=["introduction", "basics"],
            skills_taught=[PROGRAMMING_SKILLS[0].id]
        ),
        Lesson(
            title="Variables and Data Types",
            description="Understanding variables and data types in Python",
            order=2,
            content_type=ContentType.INTERACTIVE,
            text_content="""
# Variables and Data Types

## Variables
A variable is like a container that stores data.

```python
name = "Alice"
age = 15
height = 1.65
```

## Data Types
- **String**: Text data (e.g., "Hello")
- **Integer**: Whole numbers (e.g., 42)
- **Float**: Decimal numbers (e.g., 3.14)
- **Boolean**: True/False values

## Practice Exercise
Create variables for your name, age, and favorite color.
            """.strip(),
            duration_minutes=30,
            bsl_available=True,
            captions_available=True,
            prerequisite_lessons=[],  # First lesson has no prerequisites
            skills_taught=[PROGRAMMING_SKILLS[0].id, PROGRAMMING_SKILLS[1].id],
            difficulty_level=DifficultyLevel.BEGINNER,
            tags=["variables", "data_types"]
        ),
        Lesson(
            title="Making Decisions with If Statements",
            description="Learn to control program flow with conditional logic",
            order=3,
            content_type=ContentType.VIDEO,
            duration_minutes=25,
            bsl_available=True,
            captions_available=True,
            prerequisite_lessons=[
                "Welcome to Python",
                "Variables and Data Types"
            ],
            prerequisite_skills=[PROGRAMMING_SKILLS[0].id, PROGRAMMING_SKILLS[1].id],
            skills_taught=[PROGRAMMING_SKILLS[2].id],
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            tags=["control_flow", "conditionals"],
            text_content="""
# Making Decisions with If Statements

## If Statements
If statements let your code make decisions.

```python
age = 18

if age >= 18:
    print("You are an adult")
else:
    print("You are a minor")
```

## Comparison Operators
- `==` Equal to
- `!=` Not equal to
- `>` Greater than
- `<` Less than
- `>=` Greater or equal
- `<=` Less or equal

## Practice
Write a program that checks if a number is positive, negative, or zero.
            """.strip()
        ),
        Lesson(
            title="Loops: Repeating Code",
            description="Use loops to repeat actions efficiently",
            order=4,
            content_type=ContentType.INTERACTIVE,
            duration_minutes=35,
            bsl_available=True,
            captions_available=True,
            prerequisite_skills=[PROGRAMMING_SKILLS[2].id],
            skills_taught=[PROGRAMMING_SKILLS[2].id],
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            tags=["loops", "control_flow"],
            text_content="""
# Loops: Repeating Code

## For Loops
Repeat code a specific number of times.

```python
for i in range(5):
    print(i)
```

## While Loops
Repeat code while a condition is true.

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

## Practice
Write a program that prints the multiplication table for a number.
            """.strip()
        ),
        Lesson(
            title="Final Project: Build a Calculator",
            description="Apply what you've learned to build a working calculator",
            order=5,
            content_type=ContentType.PROJECT,
            duration_minutes=45,
            bsl_available=True,
            captions_available=True,
            prerequisite_skills=[skill.id for skill in PROGRAMMING_SKILLS],
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            tags=["project", "assessment"],
            text_content="""
# Final Project: Build a Calculator

## Your Task
Create a calculator program that can:
1. Add two numbers
2. Subtract two numbers
3. Multiply two numbers
4. Divide two numbers

## Requirements
- Ask the user which operation to perform
- Get two numbers from the user
- Display the result
- Handle division by zero
- Use BSL-friendly output

## Example
```python
print("Calculator")
print("1. Add")
print("2. Subtract")
# ... your code here
```

## Success Criteria
- Program works correctly
- Code is well-organized
- Error handling included
- User-friendly output
            """.strip()
        )
    ],
    is_published=True
)


# Example Assessment
VARIABLES_QUIZ = Assessment(
    title="Variables and Data Types Quiz",
    description="Test your understanding of variables and data types",
    assessment_type=AssessmentType.QUIZ,
    time_limit_minutes=10,
    passing_score_threshold=0.7,
    max_attempts=3,
    show_feedback=True,
    skills_assessed=[PROGRAMMING_SKILLS[0].id, PROGRAMMING_SKILLS[1].id],
    questions=[
        {
            "question": "What data type is 'Hello, World!'?",
            "options": ["Integer", "String", "Float", "Boolean"],
            "correct_answer": "String",
            "points": 1,
            "explanation": "Text enclosed in quotes is a string data type."
        },
        {
            "question": "Which of these is a valid variable name?",
            "options": ["2nd_place", "user_name", "class", "user-name"],
            "correct_answer": "user_name",
            "points": 1,
            "explanation": "Variable names cannot start with numbers or contain hyphens."
        },
        {
            "question": "What is the result of: int(3.7)?",
            "options": ["3.7", "3", "4", "Error"],
            "correct_answer": "3",
            "points": 1,
            "explanation": "int() truncates the decimal part, not rounds."
        },
        {
            "question": "How do you convert a string to an integer?",
            "options": ["integer()", "int()", "to_int()", "convert()"],
            "correct_answer": "int()",
            "points": 1,
            "explanation": "int() is the built-in function for integer conversion."
        },
        {
            "question": "What is the data type of True?",
            "options": ["String", "Integer", "Boolean", "Float"],
            "correct_answer": "Boolean",
            "points": 1,
            "explanation": "True and False are boolean values."
        }
    ]
)


# Example Practical Assessment
CONTROL_FLOW_PRACTICAL = Assessment(
    title="Control Flow Practical Assessment",
    description="Write code to solve programming problems",
    assessment_type=AssessmentType.PRACTICAL,
    time_limit_minutes=30,
    passing_score_threshold=0.6,
    max_attempts=2,
    show_feedback=True,
    skills_assessed=[PROGRAMMING_SKILLS[2].id],
    questions=[
        {
            "question": "Write a program that checks if a number is even or odd.",
            "starter_code": "# Write your code here\nnumber = 7\n\n# Your code",
            "solution_template": "if number % 2 == 0:\n    print('Even')\nelse:\n    print('Odd')",
            "points": 5,
            "rubric": {
                "excellent": "Correct logic, proper syntax, clear output",
                "good": "Correct logic with minor syntax issues",
                "satisfactory": "Partial implementation",
                "needs_improvement": "Incorrect or incomplete"
            }
        },
        {
            "question": "Write a program that prints numbers 1-10 using a loop.",
            "starter_code": "# Write your code here\n\n# Your loop",
            "solution_template": "for i in range(1, 11):\n    print(i)",
            "points": 5,
            "rubric": {
                "excellent": "Correct loop with proper range",
                "good": "Working loop with minor issues",
                "satisfactory": "Partial implementation",
                "needs_improvement": "Incorrect approach"
            }
        }
    ]
)


def get_example_curriculum():
    """Get complete example curriculum."""
    return {
        "educator": EXAMPLE_EDUCATOR,
        "course": INTRO_TO_PYTHON_COURSE,
        "skills": PROGRAMMING_SKILLS,
        "assessments": {
            "variables_quiz": VARIABLES_QUIZ,
            "control_flow_practical": CONTROL_FLOW_PRACTICAL
        }
    }


def print_example_curriculum():
    """Print example curriculum for demonstration."""
    curriculum = get_example_curriculum()

    print("=" * 80)
    print("EXAMPLE EDUCATIONAL CURRICULUM")
    print("=" * 80)
    print()

    print(f"EDUCATOR: {curriculum['educator'].name}")
    print(f"  Email: {curriculum['educator'].email}")
    print(f"  Institution: {curriculum['educator'].institution}")
    print(f"  Department: {curriculum['educator'].department}")
    print(f"  Expertise: {', '.join(curriculum['educator'].areas_of_expertise)}")
    print()

    print(f"COURSE: {curriculum['course'].title}")
    print(f"  Subject: {curriculum['course'].subject}")
    print(f"  Grade Level: {curriculum['course'].grade_level}")
    print(f"  Difficulty: {curriculum['course'].difficulty_level.value}")
    print(f"  Duration: {curriculum['course'].estimated_duration_hours} hours")
    print()

    print("LESSONS:")
    for lesson in curriculum['course'].lessons:
        print(f"  {lesson.order}. {lesson.title}")
        print(f"     Type: {lesson.content_type.value}")
        print(f"     Duration: {lesson.duration_minutes} min")
        if lesson.bsl_available:
            print(f"     ✓ BSL available")
        if lesson.captions_available:
            print(f"     ✓ Captions available")
        print()

    print("SKILLS TAUGHT:")
    for skill in curriculum['skills']:
        print(f"  • {skill.name} ({skill.difficulty_level.value})")
        print(f"    {skill.description}")
    print()

    print("ASSESSMENTS:")
    for name, assessment in curriculum['assessments'].items():
        print(f"  • {assessment.title}")
        print(f"    Type: {assessment.assessment_type.value}")
        print(f"    Questions: {len(assessment.questions)}")
        print(f"    Passing: {assessment.passing_score_threshold * 100}%")
    print()

    print("=" * 80)


if __name__ == "__main__":
    print_example_curriculum()
