import streamlit as st
import pandas as pd
from agent import ApiEstimate, AnalysisResult, analyze_features, format_output
import json
from typing import List
from dotenv import load_dotenv
import os

load_dotenv("../.env")
# print(os.getenv("OPENAI_API_KEY"))

def calculate_total_estimate(apis: List[ApiEstimate]) -> float:
    return sum(api.estimate for api in apis)

def format_output(analysis_result: AnalysisResult) -> str:
    output_lines = [
        f"- {api.method} {api.path} - {api.description} ({api.estimate} manday)"
        for api in analysis_result.apis
    ]
    
    output = "\n".join(output_lines)
    output += f"\n\nTổng lượng thời gian ước lượng: {analysis_result.total_estimate} (tính theo manday, 1 manday = 7hour)"
    
    return output



def estimate_features(input_text: str) -> str:
    """
    Main function to analyze features and generate estimation output
    """
    analysis = analyze_features(input_text)
    return format_output(analysis)

def run_app():
    st.title("Feature Estimation Tool")

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input Features")
        feature_input = st.text_area(
            "Enter features to analyze",
            height=400,
            placeholder="Enter feature requirements here..."
        )

        if st.button("Analyze"):
            if feature_input:
                with st.spinner("Analyzing features..."):
                    try:
                        # Get analysis result
                        result = estimate_features(feature_input)
                        
                        # Parse the result back into structured data
                        apis_list = []
                        total = 0
                        
                        for line in result.split('\n'):
                            if line.startswith('-'):
                                # Parse API line
                                parts = line.split(' - ')
                                if len(parts) == 2:
                                    method_path = parts[0].strip('- ')
                                    desc_est = parts[1].rsplit('(', 1)
                                    
                                    method = method_path.split()[0]
                                    path = method_path.split()[1]
                                    description = desc_est[0].strip()
                                    estimate = float(desc_est[1].strip('()manday'))
                                    
                                    apis_list.append({
                                        'Method': method,
                                        'Path': path,
                                        'Description': description,
                                        'Estimate (manday)': estimate
                                    })
                            elif 'Tổng lượng thời gian ước lượng:' in line:
                                total = float(line.split(':')[1].split('(')[0].strip())

                        # Store in session state
                        st.session_state['analysis_result'] = {
                            'apis': apis_list,
                            'total': total
                        }

                    except Exception as e:
                        st.error(f"Error analyzing features: {str(e)}")

    with col2:
        st.subheader("Estimation Results")
        if 'analysis_result' in st.session_state:
            result = st.session_state['analysis_result']
            
            # Display APIs table
            df = pd.DataFrame(result['apis'])
            st.dataframe(
                df,
                column_config={
                    'Method': st.column_config.TextColumn('Method', width=100),
                    'Path': st.column_config.TextColumn('Path', width=200),
                    'Description': st.column_config.TextColumn('Description', width=300),
                    'Estimate (manday)': st.column_config.NumberColumn(
                        'Estimate (manday)',
                        format="%.1f",
                        width=150
                    )
                }
            )
            
            # Display total
            st.metric(
                label="Total Estimation", 
                value=f"{result['total']:.1f} mandays",
                help="1 manday = 7 hours"
            )

if __name__ == '__main__':
    run_app()
