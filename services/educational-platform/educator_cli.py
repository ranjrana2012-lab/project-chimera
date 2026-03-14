"""Simple CLI Interface for Educators.

Command-line interface for educators to manage courses, students, and monitor progress.
"""

import asyncio
import json
from typing import Optional
from datetime import datetime
import httpx


class EducatorCLI:
    """CLI interface for educators."""

    def __init__(self, base_url: str = "http://localhost:8012"):
        """Initialize CLI."""
        self.base_url = base_url
        self.educator_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_educator_profile(
        self,
        name: str,
        email: str,
        institution: str,
        department: str = "",
        subjects: list = None
    ) -> dict:
        """Create educator profile."""
        from models import EducatorProfile

        educator = EducatorProfile(
            name=name,
            email=email,
            institution=institution,
            department=department,
            subjects=subjects or [],
            areas_of_expertise=[],
            qualifications=[],
            years_of_experience=0
        )

        response = await self.client.post(
            f"{self.base_url}/api/v1/educators",
            json=educator.model_dump()
        )

        if response.status_code == 200:
            data = response.json()
            self.educator_id = data["data"]["educator_id"]
            return data
        else:
            raise Exception(f"Failed to create educator: {response.text}")

    async def create_course(
        self,
        title: str,
        description: str,
        subject: str,
        grade_level: str,
        lessons: list = None
    ) -> dict:
        """Create a new course."""
        if not self.educator_id:
            raise Exception("Educator profile not created. Call create_educator_profile() first.")

        from models import Course, Lesson, DifficultyLevel

        course = Course(
            title=title,
            description=description,
            subject=subject,
            grade_level=grade_level,
            educator_id=self.educator_id,
            educator_name="",  # Will be filled by service
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            lessons=[Lesson(**l) if isinstance(l, dict) else l for l in (lessons or [])]
        )

        response = await self.client.post(
            f"{self.base_url}/api/v1/courses",
            json=course.model_dump()
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to create course: {response.text}")

    async def list_courses(self, educator_id: Optional[str] = None) -> list:
        """List all courses."""
        params = {}
        if educator_id:
            params["educator_id"] = educator_id

        response = await self.client.get(
            f"{self.base_url}/api/v1/courses",
            params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list courses: {response.text}")

    async def create_student(
        self,
        name: str,
        email: str,
        grade_level: str,
        institution: str = "",
        learning_style: str = "multimodal",
        requires_bsl: bool = False,
        requires_captions: bool = False
    ) -> dict:
        """Create a student profile."""
        from models import StudentProfile, AccessibilityNeeds, LearningStyle

        student = StudentProfile(
            name=name,
            email=email,
            grade_level=grade_level,
            institution=institution,
            learning_style=LearningStyle(learning_style),
            accessibility_needs=AccessibilityNeeds(
                requires_bsl=requires_bsl,
                requires_captions=requires_captions
            )
        )

        response = await self.client.post(
            f"{self.base_url}/api/v1/students",
            json=student.model_dump()
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to create student: {response.text}")

    async def enroll_student(self, student_id: str, course_id: str) -> dict:
        """Enroll a student in a course."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/enrollments",
            params={
                "student_id": student_id,
                "course_id": course_id
            }
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to enroll student: {response.text}")

    async def get_student_analytics(self, student_id: str, days: int = 30) -> dict:
        """Get student analytics."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/students/{student_id}/analytics",
            params={"days": days}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get analytics: {response.text}")

    async def get_classroom_sentiment(self, course_id: str) -> dict:
        """Get classroom sentiment."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/sentiment/classroom/{course_id}"
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get sentiment: {response.text}")

    async def enhance_content(
        self,
        content: str,
        student_id: str,
        session_id: str
    ) -> dict:
        """Enhance content with accessibility features."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/content/enhance",
            params={
                "content": content,
                "student_id": student_id,
                "session_id": session_id
            }
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to enhance content: {response.text}")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


async def interactive_cli():
    """Interactive CLI for educators."""
    print("=" * 80)
    print("EDUCATIONAL PLATFORM - EDUCATOR CLI")
    print("=" * 80)
    print()

    cli = EducatorCLI()

    try:
        # Get educator info
        print("Create your educator profile:")
        name = input("Name: ")
        email = input("Email: ")
        institution = input("Institution: ")
        department = input("Department (optional): ")

        # Create educator
        print("\nCreating educator profile...")
        result = await cli.create_educator_profile(
            name=name,
            email=email,
            institution=institution,
            department=department
        )
        educator_id = result["data"]["educator_id"]
        print(f"✓ Educator profile created: {educator_id}")

        # Main menu
        while True:
            print("\n" + "=" * 80)
            print("MAIN MENU")
            print("=" * 80)
            print("1. Create a new course")
            print("2. List all courses")
            print("3. Create a student profile")
            print("4. Enroll student in course")
            print("5. View student analytics")
            print("6. Monitor classroom sentiment")
            print("7. Enhance content with accessibility")
            print("8. Exit")
            print()

            choice = input("Select option (1-8): ").strip()

            if choice == "1":
                # Create course
                print("\nCREATE NEW COURSE")
                title = input("Course title: ")
                description = input("Description: ")
                subject = input("Subject: ")
                grade_level = input("Grade level: ")

                print("\nCreating course...")
                result = await cli.create_course(
                    title=title,
                    description=description,
                    subject=subject,
                    grade_level=grade_level
                )
                print(f"✓ Course created: {result['data']['course_id']}")

            elif choice == "2":
                # List courses
                print("\nALL COURSES")
                courses = await cli.list_courses(educator_id=educator_id)
                for course in courses:
                    print(f"  • {course['title']} ({course['id']})")
                    print(f"    {course['subject']} - {course['grade_level']}")

            elif choice == "3":
                # Create student
                print("\nCREATE STUDENT PROFILE")
                name = input("Student name: ")
                email = input("Student email: ")
                grade_level = input("Grade level: ")
                institution = input("Institution: ")

                print("\nAccessibility needs:")
                requires_bsl = input("Requires BSL (y/n): ").lower() == 'y'
                requires_captions = input("Requires captions (y/n): ").lower() == 'y'

                print("\nCreating student profile...")
                result = await cli.create_student(
                    name=name,
                    email=email,
                    grade_level=grade_level,
                    institution=institution,
                    requires_bsl=requires_bsl,
                    requires_captions=requires_captions
                )
                print(f"✓ Student profile created: {result['data']['student_id']}")

            elif choice == "4":
                # Enroll student
                print("\nENROLL STUDENT")
                student_id = input("Student ID: ")
                course_id = input("Course ID: ")

                print("\nEnrolling student...")
                result = await cli.enroll_student(student_id, course_id)
                print(f"✓ Student enrolled: {result['data']['enrollment_id']}")

            elif choice == "5":
                # View analytics
                print("\nSTUDENT ANALYTICS")
                student_id = input("Student ID: ")
                days = input("Days to analyze (default 30): ") or "30"

                analytics = await cli.get_student_analytics(student_id, int(days))
                print(f"\nAnalytics for {student_id}:")
                print(f"  Total sessions: {analytics['total_sessions']}")
                print(f"  Learning time: {analytics['total_learning_time_minutes']} minutes")
                print(f"  Average engagement: {analytics['average_engagement_score']:.2f}")
                print(f"  Assessments completed: {analytics['assessments_completed']}")
                print(f"  Average score: {analytics['average_assessment_score']:.2f}")

            elif choice == "6":
                # Monitor sentiment
                print("\nCLASSROOM SENTIMENT")
                course_id = input("Course ID: ")

                sentiment = await cli.get_classroom_sentiment(course_id)
                print(f"\nSentiment data for {course_id}:")
                print(json.dumps(sentiment, indent=2))

            elif choice == "7":
                # Enhance content
                print("\nENHANCE CONTENT WITH ACCESSIBILITY")
                content = input("Content text: ")
                student_id = input("Student ID: ")
                session_id = input("Session ID: ")

                enhanced = await cli.enhance_content(content, student_id, session_id)
                print(f"\nEnhanced content:")
                print(json.dumps(enhanced, indent=2))

            elif choice == "8":
                print("\nGoodbye!")
                break

            else:
                print("\nInvalid option. Please try again.")

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await cli.close()


async def quick_demo():
    """Quick demo of CLI functionality."""
    print("=" * 80)
    print("EDUCATIONAL PLATFORM - QUICK DEMO")
    print("=" * 80)
    print()

    cli = EducatorCLI()

    try:
        # Create educator
        print("1. Creating educator profile...")
        result = await cli.create_educator_profile(
            name="Dr. Sarah Chen",
            email="sarah.chen@bmet.ac.uk",
            institution="BMet College",
            department="Digital Technologies"
        )
        educator_id = result["data"]["educator_id"]
        print(f"   ✓ Educator created: {educator_id}")

        # Create course
        print("\n2. Creating course...")
        result = await cli.create_course(
            title="Introduction to Python",
            description="Learn Python programming fundamentals",
            subject="Computer Science",
            grade_level="Year 10"
        )
        course_id = result["data"]["course_id"]
        print(f"   ✓ Course created: {course_id}")

        # Create students
        print("\n3. Creating students...")
        result1 = await cli.create_student(
            name="Alex Johnson",
            email="alex.johnson@bmet.ac.uk",
            grade_level="Year 10",
            institution="BMet College",
            requires_bsl=True,
            requires_captions=True
        )
        student1_id = result1["data"]["student_id"]
        print(f"   ✓ Student 1 created (BSL + captions): {student1_id}")

        result2 = await cli.create_student(
            name="Maria Garcia",
            email="maria.garcia@bmet.ac.uk",
            grade_level="Year 10",
            institution="BMet College",
            requires_captions=True
        )
        student2_id = result2["data"]["student_id"]
        print(f"   ✓ Student 2 created (captions): {student2_id}")

        # Enroll students
        print("\n4. Enrolling students...")
        await cli.enroll_student(student1_id, course_id)
        print(f"   ✓ Alex enrolled")
        await cli.enroll_student(student2_id, course_id)
        print(f"   ✓ Maria enrolled")

        # Enhance content
        print("\n5. Enhancing content with accessibility...")
        enhanced = await cli.enhance_content(
            content="Welcome to Python programming!",
            student_id=student1_id,
            session_id="demo_session"
        )
        print(f"   ✓ Content enhanced with: {', '.join(enhanced['data'].get('accessibility_features', []))}")

        print("\n" + "=" * 80)
        print("DEMO COMPLETE!")
        print("=" * 80)
        print(f"\nEducator ID: {educator_id}")
        print(f"Course ID: {course_id}")
        print(f"Student 1 ID: {student1_id}")
        print(f"Student 2 ID: {student2_id}")
        print("\nYou can now use the API or web interface to continue!")
        print()

    except Exception as e:
        print(f"\nDemo error: {e}")
    finally:
        await cli.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        asyncio.run(quick_demo())
    else:
        asyncio.run(interactive_cli())
