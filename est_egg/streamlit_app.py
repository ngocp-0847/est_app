import streamlit as st
import os
import tempfile
import re
from est_egg.software_analyst_agent import SoftwareAnalystAgent
import streamlit.components.v1 as components
import pandas as pd

def display_task_hierarchy(tasks, level=0):
    """Render task breakdown as markdown with proper indentation"""
    result = ""
    for task in tasks:
        difficulty = f"({task.difficulty})" if task.difficulty else ""
        estimate = f"Est: {task.time_estimate}" if task.time_estimate else ""
        result += f"{'  ' * level}- **{task.task_name}** {difficulty} {estimate}\n"
        if task.description:
            result += f"{'  ' * (level+1)}{task.description}\n"
        if task.subtasks:
            result += display_task_hierarchy(task.subtasks, level + 1)
    return result

def convert_to_mandays(time_estimate_str):
    """Convert a time estimate string to mandays (1 manday = 7 hours)"""
    if not time_estimate_str:
        return ""
    
    # Check for hours
    hours_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours|hour|hrs|hr|h)', time_estimate_str, re.IGNORECASE)
    if hours_match:
        hours = float(hours_match.group(1))
        mandays = hours / 7
        return f"{mandays:.2f}"
    
    # Check for days
    days_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:days|day|d)', time_estimate_str, re.IGNORECASE)
    if days_match:
        days = float(days_match.group(1))
        return f"{days:.2f}"
    
    # If the format is not recognized, return the original
    return time_estimate_str

def build_task_table(tasks):
    """Build table data from task hierarchy"""
    task_rows = []
    
    def process_task(task, depth=0):
        # Convert time estimate to mandays if it exists
        estimate = task.time_estimate if task.time_estimate else ""
        manday_estimate = convert_to_mandays(estimate)
        
        # Add the task to the data with appropriate indentation
        row = {
            "Task Name": "• " * depth + task.task_name,
            "Difficulty": task.difficulty if task.difficulty else "",
            "Description": task.description if task.description else "",
            "Estimated Time (mandays)": manday_estimate,
            "Original Estimate": estimate
        }
        task_rows.append(row)
        
        # Process subtasks
        if task.subtasks:
            for subtask in task.subtasks:
                process_task(subtask, depth + 1)
    
    # Process all top-level tasks
    for task in tasks:
        process_task(task)
    
    return task_rows

def display_api_endpoints(apis):
    """Render API endpoints as markdown"""
    result = ""
    for api in apis:
        result += f"### {api.method} {api.endpoint}\n"
        if api.purpose:
            result += f"**Purpose**: {api.purpose}\n\n"
        
        if api.request_params:
            result += "**Request Parameters:**\n```json\n"
            result += str(api.request_params).replace("'", "\"") + "\n"
            result += "```\n\n"
        
        if api.response_structure:
            result += "**Response Structure:**\n```json\n"
            result += str(api.response_structure).replace("'", "\"") + "\n"
            result += "```\n\n"
    return result

def display_entities(entities):
    """Render entities as markdown"""
    result = ""
    for entity in entities:
        result += f"### {entity.entity_name}\n"
        
        if entity.attributes:
            result += "**Attributes:**\n```\n"
            for attr, type_info in entity.attributes.items():
                result += f"{attr}: {type_info}\n"
            result += "```\n\n"
        
        if entity.relationships:
            result += "**Relationships:**\n"
            for rel in entity.relationships:
                result += f"- {rel}\n"
            result += "\n"
    return result

def render_mermaid(mermaid_code):
    """Render Mermaid diagram using HTML component"""
    # This uses mermaid.js for rendering
    html = f"""
    <div class="mermaid">
    {mermaid_code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
    components.html(html, height=500)

def merge_requirements(text_requirement, uploaded_files):
    """Merge requirements from text input and uploaded files"""
    requirements = []
    
    # Add text requirement if provided
    if text_requirement and text_requirement.strip():
        requirements.append(text_requirement.strip())
    
    # Process uploaded files
    file_contents = []
    for uploaded_file in uploaded_files:
        content = uploaded_file.read().decode("utf-8")
        file_contents.append(f"## From file: {uploaded_file.name}\n{content}")
    
    # Add file contents to requirements
    if file_contents:
        requirements.append("\n\n".join(file_contents))
    
    # Merge all requirements
    return "\n\n---\n\n".join(requirements)

def main():
    st.set_page_config(
        page_title="Software Requirement Analyzer", 
        page_icon="📊", 
        layout="wide"
    )
    
    st.title("Software Requirement Analyzer")
    st.markdown("Analyze software requirements to get task breakdowns, API designs, and entity-relationship diagrams.")
    
    # Initialize session states if needed
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("OPENAI_API_KEY", "")
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    
    # Sidebar for input configuration
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", value=st.session_state.api_key, type="password")
    st.session_state.api_key = api_key
    
    # Replace radio buttons with checkboxes to allow multiple selections
    st.header("Requirement Input")
    col1, col2 = st.columns(2)
    with col1:
        use_text_input = st.checkbox("Use Text Input", value=True)
    with col2:
        use_file_input = st.checkbox("Use Markdown Files", value=False)
    
    requirement_text = ""
    uploaded_files = []
    
    if use_text_input:
        requirement_text = st.text_area(
            "Enter your software requirement:",
            height=200,
            placeholder="Example: Implement a user authentication system with registration, login, password reset, and OAuth integration."
        )
    
    if use_file_input:
        uploaded_files = st.file_uploader("Upload markdown files", type=["md"], accept_multiple_files=True)
        
        if uploaded_files:
            st.subheader("File Previews")
            for i, uploaded_file in enumerate(uploaded_files):
                with st.expander(f"Preview: {uploaded_file.name}"):
                    content = uploaded_file.read().decode("utf-8")
                    uploaded_file.seek(0)  # Reset file pointer after reading
                    st.text_area(f"File {i+1} content:", value=content[:500] + ("..." if len(content) > 500 else ""), height=150, disabled=True)
    
    if st.button("Analyze Requirements"):
        # Check if any inputs are provided
        if not requirement_text.strip() and not uploaded_files:
            st.error("Please provide at least one input method (text or files).")
            return
            
        if not api_key:
            st.error("Please provide your OpenAI API key.")
            return
            
        try:
            with st.spinner("Analyzing requirements..."):
                analyst = SoftwareAnalystAgent(api_key=api_key)
                
                if uploaded_files and not requirement_text.strip():
                    # Only file uploads
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_files = []
                        for uploaded_file in uploaded_files:
                            temp_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            temp_files.append(temp_path)
                        
                        results = analyst.analyze_from_multiple_markdown(temp_files)
                
                elif requirement_text.strip() and not uploaded_files:
                    # Only text input
                    results = analyst.analyze_from_text(requirement_text)
                
                else:
                    # Both inputs - merge them
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_files = []
                        for uploaded_file in uploaded_files:
                            temp_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            temp_files.append(temp_path)
                        
                        merged_requirement = merge_requirements(requirement_text, uploaded_files)
                        results = analyst.analyze_from_text(merged_requirement)
                
                st.session_state.analysis_results = results
                st.success("Analysis complete!")
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
    
    # Display results if available
    if st.session_state.analysis_results:
        st.header("Analysis Results")
        results = st.session_state.analysis_results
        
        # Create tabs for different sections
        tabs = st.tabs([
            "Summary", 
            "Task Breakdown", 
            "API Endpoints", 
            "Entity Relationships", 
            "Risks & Questions",
            "Diagrams"
        ])
        
        # Tab 1: Summary
        with tabs[0]:
            st.subheader("Requirement Summary")
            st.markdown(results.summary)
            if results.total_estimate:
                st.info(f"**Total Estimated Time**: {results.total_estimate}")
        
        # Tab 2: Task Breakdown
        with tabs[1]:
            st.subheader("Task Breakdown")
            
            # Create a table for task breakdown
            task_data = build_task_table(results.task_breakdown)
            if task_data:
                df = pd.DataFrame(task_data)
                # Hide the original estimate column but keep it for reference
                columns_to_display = ["Task Name", "Difficulty", "Description", "Estimated Time (mandays)"]
                st.dataframe(
                    df[columns_to_display],
                    hide_index=True,
                    use_container_width=True
                )
                
                # Show the raw breakdown as well (optional - can be expanded)
                with st.expander("View Hierarchical Breakdown"):
                    task_md = display_task_hierarchy(results.task_breakdown)
                    st.markdown(task_md)
            else:
                st.info("No task breakdown available.")
        
        # Tab 3: API Endpoints
        with tabs[2]:
            st.subheader("API Endpoint Design")
            if results.api_analysis:
                api_md = display_api_endpoints(results.api_analysis)
                st.markdown(api_md)
            else:
                st.info("No API endpoints specified in the analysis.")
        
        # Tab 4: Entity Relationships
        with tabs[3]:
            st.subheader("Entity Relationship Analysis")
            if results.erd_analysis:
                erd_md = display_entities(results.erd_analysis)
                st.markdown(erd_md)
            else:
                st.info("No entities specified in the analysis.")
        
        # Tab 5: Risks & Questions
        with tabs[4]:
            st.subheader("Risks and Considerations")
            if results.risks_and_considerations:
                for risk in results.risks_and_considerations:
                    st.markdown(f"- {risk}")
            else:
                st.info("No risks identified.")
                
            st.subheader("Suggested Follow-up Questions")
            if results.suggested_questions:
                for question in results.suggested_questions:
                    st.markdown(f"- {question}")
            else:
                st.info("No follow-up questions suggested.")
        
        # Tab 6: Diagrams
        with tabs[5]:
            st.subheader("Task Hierarchy Diagram")
            if results.mermaid_task_diagram:
                render_mermaid(results.mermaid_task_diagram)
                st.markdown("**Mermaid Code:**")
                st.code(results.mermaid_task_diagram, language="mermaid")
            else:
                st.info("No task diagram available.")
                
            st.subheader("Entity Relationship Diagram")
            if results.mermaid_erd_diagram:
                render_mermaid(results.mermaid_erd_diagram)
                st.markdown("**Mermaid Code:**")
                st.code(results.mermaid_erd_diagram, language="mermaid")
            else:
                st.info("No ERD diagram available.")

def run_streamlit():
    """Entry point for running the Streamlit app."""
    import sys
    import streamlit.web.bootstrap
    
    # Get the directory of the current file
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "streamlit_app.py")
    
    # Run the Streamlit app
    args = []
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    streamlit.web.bootstrap.run(filename, "", args, [])

if __name__ == "__main__":
    main()
