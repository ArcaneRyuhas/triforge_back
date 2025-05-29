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
Assistant: """
}