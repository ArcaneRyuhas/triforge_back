PROMPT_TEMPLATES = {
    "jira_generation": """Generate Jira user stories for the following software requirement:

"{requirement}"

For each user story:
1. Create a clear title in the format "As a [user type], I want to [action] so that [benefit]"
2. Add a detailed description
3. Add acceptance criteria (at least 3 per story)
4. Assign story points (1, 2, 3, 5, 8, 13)
5. Set priority (Highest, High, Medium, Low, Lowest)

Create at least 5 user stories that cover the main functionality.
Format the output in Markdown with each story as a separate section.

Chat History:
{chat_history}
""",

    "jira_modification": """You are reviewing and modifying a set of Jira user stories based on additional requirements or feedback.

{input}

Please modify the existing Jira stories to incorporate these additional requirements. You can:
1. Update existing story titles, descriptions, or acceptance criteria
2. Add new acceptance criteria to existing stories
3. Add entirely new stories if needed
4. Adjust story points or priorities if appropriate
5. Do not add any nodes or edges unless explicitly requested
6. Do not refactor existing flows unless instructed

Maintain the same format as the original stories and highlight changes with [MODIFIED] or [NEW] tags.

Chat History:
{chat_history}
""",

    "diagram_generation": """You are a software architect who creates diagrams based on Jira user stories.

{input}

Please create a diagram that represents the system described in these Jira stories.
Return ONLY the Mermaid.js code without any explanations or markdown blocks.

Chat History:
{chat_history}
""",

    "diagram_modification": """You are a software architect who modifies existing Mermaid.js diagrams.

{input}

Please modify the provided Mermaid.js diagram based strictly on the "Modification Request".
Return the complete, valid Mermaid.js code without explanations or markdown blocks.

Chat History:
{chat_history}
""",

    "code_generation": """You are a senior software engineer. Generate clean, functional code for the system described.

{input}

Return ONLY the code without explanations or markdown blocks.

Chat History:
{chat_history}
""",

    "code_modification": """You are a senior software engineer who modifies existing code.

{input}

Modify the provided code based strictly on the "Modification Request".
Return the complete, functional code without explanations or markdown blocks.

Chat History:
{chat_history}
""",

    "conversation": """You are a helpful assistant. Answer the user's question based on the conversation history.

Chat History:
{chat_history}

User: {input}
Assistant: 
""",

    "validation_requirements": """I will give you requirements, i want you to grade the requirements and give me a true if requirements
    are graded 7 or above, otherwise false.

The answer should be only: false or true

Don't give me any more details.

Requirements:

{requirement}

""",

# Add these to src/utils/prompts.py in the PROMPT_TEMPLATES dictionary

    "technology_detection": """You are a senior software architect. Analyze the user prompt and identify the technologies they want to use.

User Prompt: "{prompt}"

Available Context from Memory:
{context}

Extract and return a JSON object with the following structure:
{{
  "technologies": [
    {{
      "name": "technology name",
      "category": "frontend|backend|database|mobile|devops|testing|other",
      "version": "version if specified or null"
    }}
  ]
}}

Focus only on explicitly mentioned technologies. If the user mentions general terms, infer the most common/recommended technology for that category.

Examples:
- "Next.js" -> frontend
- "Node.js", "Express", "Nest.js" -> backend  
- "MongoDB", "PostgreSQL", "MySQL" -> database
- "React Native", "Flutter" -> mobile
- "Docker", "Kubernetes" -> devops

Return only valid JSON, no explanations.""",

    "project_code_generation": """You are a senior full-stack developer. Generate a complete, production-ready project structure with all necessary files.

{input}

Generate a complete project with:
1. Proper folder structure following best practices for each technology
2. Configuration files (package.json, .env.example, etc.)
3. Main application files with basic functionality
4. Database models/schemas if applicable
5. API routes/endpoints if backend is included
6. Frontend components if frontend is included
7. Security implementations (authentication, validation, etc.)
8. Error handling and logging
9. Basic tests
10. Documentation files

Return a JSON object with this structure:
{{
  "files": [
    {{
      "path": "relative/file/path.ext",
      "content": "complete file content",
      "language": "javascript|typescript|python|html|css|json|markdown|yaml|etc"
    }}
  ]
}}

Important guidelines:
- Use modern best practices and patterns
- Include proper error handling and security measures
- Create a scalable, maintainable structure
- Add comments explaining key functionality
- Include environment configuration
- Follow naming conventions for each technology
- Create at least 15-25 files for a complete project
- Include package.json/requirements.txt with all dependencies

Return only valid JSON, no explanations.

For the moment try to generate a project with only commentary files, no actual code. Try to make it as small as possible, but with a complete structure.
""",

# Add these to src/utils/prompts.py in the PROMPT_TEMPLATES dictionary

"requirements_refinement": """You are a senior business analyst and requirements engineer. Transform the following poorly written document into clear, well-structured software requirements.

{input}

Please transform this document into professional requirements by:
1. Identifying and extracting all functional requirements
2. Clarifying ambiguous statements
3. Filling in missing details based on common practices
4. Organizing requirements logically
5. Adding acceptance criteria for each requirement
6. Categorizing requirements (must-have, nice-to-have)
7. Identifying any non-functional requirements (performance, security, etc.)

Structure the output as follows:
- Clear requirement titles
- Detailed descriptions
- Acceptance criteria
- Priority levels
- Any technical constraints or dependencies

Make reasonable assumptions where the original document is unclear, and note these assumptions.

Chat History:
{chat_history}
""",

"requirements_analysis": """You are a requirements analyst. Analyze the following document and extract key requirements without full refinement.

{input}

Analyze and provide:
1. Main features/capabilities mentioned
2. User types or roles identified
3. Key functional areas
4. Any constraints or limitations mentioned
5. Potential gaps or missing information
6. Recommended next steps for clarification

Provide a concise analysis that helps understand what the document is trying to convey.

Chat History:
{chat_history}
""",

"intent_detection": """You are an AI assistant specialized in understanding user intent for a software development system.

Analyze the user's message and conversation context to determine their intent.

{input}

Based on the message and context, determine the user's intent. Consider:
1. Keywords and phrases in the message
2. Previous conversation context (what artifacts exist)
3. Whether this is a modification request or new creation

Possible intents:
- "conversation": General questions, clarifications, or chat
- "documentation": Creating Jira stories, requirements, or user stories
- "diagram": Creating visual diagrams (flowchart, sequence, class, etc.)
- "code": Generating project code or implementation
- "modify_documentation": Updating existing Jira stories
- "modify_diagram": Updating existing diagrams
- "modify_code": Updating existing code

Return ONLY a valid JSON response in this exact format:
{{
    "intent": "one of the intents listed above",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation of why this intent was chosen",
    "extracted_params": {{
        // Optional parameters based on intent
        // For diagram: "diagram_type": "flowchart|sequence|class|er|state|gantt|journey"
        // For code: "technologies": ["technology names mentioned"]
        // For modifications: "target": "what specifically to modify"
    }}
}}

Examples:
- "Create a flowchart for the login process" -> intent: "diagram", diagram_type: "flowchart"
- "Add authentication to the stories" -> intent: "modify_documentation"
- "Build a Next.js app with MongoDB" -> intent: "code", technologies: ["Next.js", "MongoDB"]
- "How does the system work?" -> intent: "conversation"

Chat History:
{chat_history}"""
}