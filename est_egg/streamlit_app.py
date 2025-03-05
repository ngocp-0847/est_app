import streamlit as st
import os
import tempfile
from est_egg.software_analyst_agent import SoftwareAnalystAgent
import streamlit.components.v1 as components

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
    
    input_method = st.sidebar.radio("Input Method", ["Text Input", "Markdown File"])
    
    # Main area for inputs
    st.header("Requirement Input")
    
    if input_method == "Text Input":
        requirement_text = st.text_area(
            "Enter your software requirement:",
            height=200,
            placeholder="Example: Implement a user authentication system with registration, login, password reset, and OAuth integration."
        )
        
        if st.button("Analyze Requirement"):
            if not requirement_text.strip():
                st.error("Please enter a requirement to analyze.")
                return
                
            if not api_key:
                st.error("Please provide your OpenAI API key.")
                return
                
            try:
                with st.spinner("Analyzing requirement..."):
                    analyst = SoftwareAnalystAgent(api_key=api_key)
                    results = analyst.analyze_from_text(requirement_text)
                    st.session_state.analysis_results = results
                    st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                
    else:  # Markdown File
        uploaded_file = st.file_uploader("Upload a markdown file", type=["md"])
        
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8")
            st.text_area("File preview:", value=content[:500] + ("..." if len(content) > 500 else ""), height=150, disabled=True)
            
            if st.button("Analyze File"):
                if not api_key:
                    st.error("Please provide your OpenAI API key.")
                    return
                    
                try:
                    with st.spinner("Analyzing markdown file..."):
                        # Save the uploaded content to a temporary file
                        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
                            tmp.write(content.encode())
                            temp_path = tmp.name
                            
                        # Analyze the temporary file
                        analyst = SoftwareAnalystAgent(api_key=api_key)
                        results = analyst.analyze_from_markdown(temp_path)
                        st.session_state.analysis_results = results
                        
                        # Clean up
                        os.unlink(temp_path)
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
            task_md = display_task_hierarchy(results.task_breakdown)
            st.markdown(task_md)
        
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
