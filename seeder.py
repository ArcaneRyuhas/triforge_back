"""
Database Seeder Script
Fills the database with sample data for development and testing
"""

import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables
load_dotenv()

from src.database.models.project import ProjectModel
from src.database.models.conversation_memory import ConversationMemoryModel

class DatabaseSeeder:
    """Class to seed the database with sample data"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        self.engine = create_engine(self.database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        print(f"🔗 Connected to database: {self.database_url.split('@')[1] if '@' in self.database_url else 'local'}")
    
    def clear_data(self):
        """Clear existing data (for development)"""
        print("🧹 Clearing existing data...")
        
        try:
            # Clear in order to respect foreign key constraints
            self.session.query(ConversationMemoryModel).delete()
            self.session.query(ProjectModel).delete()
            self.session.commit()
            print("✅ Data cleared successfully")
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            self.session.rollback()
            raise
    
    def create_sample_users(self):
        """Create sample user data"""
        return [
            {
                "id": "c831a390-40d1-7028-2924-81f18afe4379",  # Mario (from your logs)
                "name": "Mario",
                "email": "mario@triforge.com"
            },
            {
                "id": str(uuid4()),
                "name": "Ana Developer",
                "email": "ana@triforge.com"
            },
            {
                "id": str(uuid4()),
                "name": "Carlos Designer",
                "email": "carlos@triforge.com"
            }
        ]
    
    def create_sample_projects(self):
        """Create sample projects for testing"""
        print("📁 Creating sample projects...")
        
        users = self.create_sample_users()
        projects_created = 0
        
        # Project templates
        project_templates = [
            {
                "name": "E-commerce Platform",
                "description": "Modern e-commerce solution with React and Node.js",
                "tags": ["ecommerce", "react", "nodejs", "mongodb"],
                "settings": {
                    "auto_created": False,
                    "template": "ecommerce",
                    "technologies": ["React", "Node.js", "MongoDB", "Express"]
                }
            },
            {
                "name": "Blog Management System",
                "description": "Content management system for blogging platform",
                "tags": ["blog", "cms", "python", "django"],
                "settings": {
                    "auto_created": False,
                    "template": "blog",
                    "technologies": ["Python", "Django", "PostgreSQL"]
                }
            },
            {
                "name": "Chat Application",
                "description": "Real-time messaging application with WebSocket support",
                "tags": ["chat", "realtime", "websocket", "vue"],
                "settings": {
                    "auto_created": False,
                    "template": "chat",
                    "technologies": ["Vue.js", "Socket.io", "Express", "Redis"]
                }
            },
            {
                "name": "Analytics Dashboard",
                "description": "Business intelligence dashboard with data visualization",
                "tags": ["analytics", "dashboard", "data", "charts"],
                "settings": {
                    "auto_created": False,
                    "template": "dashboard",
                    "technologies": ["React", "D3.js", "Python", "FastAPI"]
                }
            },
            {
                "name": "Mobile App Backend",
                "description": "REST API backend for mobile application",
                "tags": ["mobile", "api", "backend", "rest"],
                "settings": {
                    "auto_created": False,
                    "template": "mobile_backend",
                    "technologies": ["FastAPI", "PostgreSQL", "Redis", "Docker"]
                }
            }
        ]
        
        try:
            for user in users:
                # Create 2-3 projects per user
                user_projects = project_templates[:3] if user["name"] == "Mario" else project_templates[2:4]
                
                for i, template in enumerate(user_projects):
                    project_id = str(uuid4())
                    created_date = datetime.utcnow() - timedelta(days=30-i*10)
                    
                    project = ProjectModel(
                        id=project_id,
                        name=f"{template['name']} - {user['name']}",
                        description=template["description"],
                        user_id=user["id"],
                        tags=template["tags"],
                        settings=template["settings"],
                        is_active=True,
                        created_at=created_date,
                        updated_at=created_date,
                        last_activity=created_date + timedelta(days=i*2)
                    )
                    
                    self.session.add(project)
                    projects_created += 1
                    
                    print(f"  📁 Created: {project.name}")
            
            self.session.commit()
            print(f"✅ Created {projects_created} sample projects")
            return projects_created
            
        except Exception as e:
            print(f"❌ Error creating projects: {e}")
            self.session.rollback()
            raise
    
    def create_sample_memories(self):
        """Create sample conversation memories"""
        print("💭 Creating sample conversation memories...")
        
        # Get all projects
        projects = self.session.query(ProjectModel).all()
        memories_created = 0
        
        # Sample conversation data
        sample_conversations = {
            "E-commerce Platform": {
                "summary": "Discussed building an e-commerce platform with React frontend, Node.js backend, and MongoDB database. Covered user authentication, product catalog, shopping cart, and payment integration requirements.",
                "recent_messages": [
                    {"type": "human", "content": "I want to build an e-commerce platform"},
                    {"type": "ai", "content": "I'll help you create an e-commerce platform. Let me generate some user stories for the core functionality including user management, product catalog, shopping cart, and checkout process."},
                    {"type": "human", "content": "Can you create a system architecture diagram?"},
                    {"type": "ai", "content": "Here's a system architecture diagram showing the React frontend, Node.js API, MongoDB database, and payment gateway integration."}
                ],
                "token_count": 1250
            },
            "Blog Management": {
                "summary": "Planned a blog management system with Django backend and PostgreSQL database. Discussed content creation workflow, user roles (admin, editor, author), and SEO optimization features.",
                "recent_messages": [
                    {"type": "human", "content": "Need a blog management system with multiple authors"},
                    {"type": "ai", "content": "I'll create user stories for a multi-author blog system with role-based permissions, content workflow, and publishing features."},
                    {"type": "human", "content": "Add SEO optimization features"},
                    {"type": "ai", "content": "Updated the requirements to include SEO features like meta tags, URL optimization, and sitemap generation."}
                ],
                "token_count": 980
            },
            "Chat Application": {
                "summary": "Designed real-time chat application architecture with WebSocket support. Covered features like private messages, group chats, file sharing, and message history with Vue.js frontend.",
                "recent_messages": [
                    {"type": "human", "content": "Build a real-time chat app with Vue.js"},
                    {"type": "ai", "content": "I'll design a real-time chat application with Vue.js frontend and Socket.io for WebSocket communication. Let me create the user stories."},
                    {"type": "human", "content": "Add file sharing capability"},
                    {"type": "ai", "content": "Added file sharing features to the chat application requirements including image, document upload and preview functionality."}
                ],
                "token_count": 1450
            }
        }
        
        try:
            for project in projects:
                # Find matching conversation template
                template_key = None
                for key in sample_conversations.keys():
                    if key.lower() in project.name.lower():
                        template_key = key
                        break
                
                if template_key:
                    template = sample_conversations[template_key]
                    
                    memory_id = str(uuid4())
                    created_date = project.created_at + timedelta(hours=1)
                    
                    memory = ConversationMemoryModel(
                        id=memory_id,
                        user_id=project.user_id,
                        project_id=project.id,
                        summary=template["summary"],
                        recent_messages=template["recent_messages"],
                        token_count=template["token_count"],
                        created_at=created_date,
                        updated_at=project.last_activity
                    )
                    
                    self.session.add(memory)
                    memories_created += 1
                    
                    print(f"  💭 Created memory for: {project.name}")
            
            self.session.commit()
            print(f"✅ Created {memories_created} conversation memories")
            return memories_created
            
        except Exception as e:
            print(f"❌ Error creating memories: {e}")
            self.session.rollback()
            raise
    
    def create_admin_project(self):
        """Create a special admin/demo project"""
        print("👑 Creating admin demo project...")
        
        try:
            admin_project_id = str(uuid4())
            admin_user_id = "admin-demo-user-" + str(uuid4())[:8]
            
            demo_project = ProjectModel(
                id=admin_project_id,
                name="TriForge AI Demo Project",
                description="Demonstration project showcasing all TriForge AI capabilities including requirements analysis, Jira story generation, diagram creation, and code generation.",
                user_id=admin_user_id,
                tags=["demo", "showcase", "full-stack", "ai-generated"],
                settings={
                    "demo": True,
                    "featured": True,
                    "technologies": ["React", "FastAPI", "PostgreSQL", "Docker"],
                    "capabilities_demonstrated": [
                        "Requirements Refinement",
                        "Jira Story Generation", 
                        "System Diagram Creation",
                        "Full-Stack Code Generation",
                        "Project Memory Management"
                    ]
                },
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=1),
                updated_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            
            # Demo conversation memory
            demo_memory = ConversationMemoryModel(
                id=str(uuid4()),
                user_id=admin_user_id,
                project_id=admin_project_id,
                summary="Comprehensive demonstration of TriForge AI platform capabilities. Generated complete project requirements, user stories, system architecture diagrams, and full-stack application code. Showcased intelligent intent detection, project-scoped memory management, and seamless workflow from concept to implementation.",
                recent_messages=[
                    {"type": "human", "content": "I need to build a modern web application with user authentication, real-time features, and analytics"},
                    {"type": "ai", "content": "I'll help you build a comprehensive web application. Let me start by refining your requirements and generating detailed user stories."},
                    {"type": "human", "content": "Create a system architecture diagram"},
                    {"type": "ai", "content": "Here's a complete system architecture diagram showing the React frontend, FastAPI backend, PostgreSQL database, Redis for caching, and WebSocket connections for real-time features."},
                    {"type": "human", "content": "Generate the full project code"},
                    {"type": "ai", "content": "I've generated a complete full-stack project with authentication, real-time features, analytics dashboard, and proper project structure. The code includes security best practices, error handling, and comprehensive documentation."}
                ],
                token_count=2500,
                created_at=datetime.utcnow() - timedelta(hours=2),
                updated_at=datetime.utcnow()
            )
            
            self.session.add(demo_project)
            self.session.add(demo_memory)
            self.session.commit()
            
            print(f"✅ Created admin demo project: {admin_project_id}")
            return admin_project_id
            
        except Exception as e:
            print(f"❌ Error creating admin project: {e}")
            self.session.rollback()
            raise
    
    def print_summary(self):
        """Print database summary"""
        print("\n📊 Database Summary:")
        print("-" * 50)
        
        project_count = self.session.query(ProjectModel).count()
        memory_count = self.session.query(ConversationMemoryModel).count()
        active_projects = self.session.query(ProjectModel).filter(ProjectModel.is_active == True).count()
        
        print(f"Total Projects: {project_count}")
        print(f"Active Projects: {active_projects}")
        print(f"Conversation Memories: {memory_count}")
        
        # Recent projects
        recent_projects = self.session.query(ProjectModel).order_by(ProjectModel.created_at.desc()).limit(5).all()
        print(f"\nRecent Projects:")
        for project in recent_projects:
            print(f"  • {project.name} ({project.user_id[:8]}...)")
    
    def seed_all(self, clear_existing=False):
        """Run all seeding operations"""
        print("🌱 Starting database seeding...")
        print("=" * 50)
        
        try:
            if clear_existing:
                self.clear_data()
            
            projects_created = self.create_sample_projects()
            memories_created = self.create_sample_memories()
            admin_project_id = self.create_admin_project()
            
            self.print_summary()
            
            print("\n🎉 Database seeding completed successfully!")
            print(f"📁 Projects created: {projects_created + 1}")  # +1 for admin project
            print(f"💭 Memories created: {memories_created + 1}")   # +1 for admin memory
            
            return True
            
        except Exception as e:
            print(f"\n❌ Seeding failed: {e}")
            return False
        finally:
            self.session.close()

def main():
    """Main function with CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed database with sample data')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
    parser.add_argument('--projects-only', action='store_true', help='Create only sample projects')
    parser.add_argument('--memories-only', action='store_true', help='Create only conversation memories')
    parser.add_argument('--admin-only', action='store_true', help='Create only admin demo project')
    
    args = parser.parse_args()
    
    try:
        seeder = DatabaseSeeder()
        
        if args.projects_only:
            if args.clear:
                seeder.clear_data()
            seeder.create_sample_projects()
        elif args.memories_only:
            seeder.create_sample_memories()
        elif args.admin_only:
            seeder.create_admin_project()
        else:
            # Run full seeding
            success = seeder.seed_all(clear_existing=args.clear)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()