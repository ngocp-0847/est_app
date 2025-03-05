from typing import Dict, List, Optional, Any
import os
import json
from datetime import datetime
from markdown_feature_parser import MarkdownFeatureParser, FeatureNode
from software_analyst_agent import SoftwareAnalysisInputSchema, SoftwareAnalysisOutputSchema, agent
from pydantic import BaseModel

class FeatureEstimate(BaseModel):
    """Structure to hold feature estimation data"""
    feature: str
    parent_feature: Optional[str] = None
    estimate: SoftwareAnalysisOutputSchema
    children: List['FeatureEstimate'] = []
    
    class Config:
        arbitrary_types_allowed = True

class FeatureEstimator:
    """Handles estimation for features extracted from markdown"""
    
    def __init__(self, agent):
        self.agent = agent
        
    def estimate_feature(self, feature_text: str, parent_feature: Optional[str] = None, 
                         child_features: Optional[List[str]] = None) -> SoftwareAnalysisOutputSchema:
        """Generate an estimate for a single feature"""
        input_data = SoftwareAnalysisInputSchema(
            requirement=feature_text
        )
        
        # Include information about the feature's context
        context = f"This is a feature"
        if parent_feature:
            context += f" that belongs to the parent feature: {parent_feature}"
        if child_features:
            child_features_str = ", ".join(child_features)
            context += f". It has the following child features: {child_features_str}"
            
        # Add context to the requirement
        input_data.requirement = f"{input_data.requirement}\n\nContext: {context}"
        
        # Run the agent to get estimation
        return self.agent.run(input_data)
    
    def estimate_from_markdown(self, markdown_path: str) -> Dict[str, FeatureEstimate]:
        """
        Process a markdown file and generate estimates for all features
        Returns a dictionary with feature titles as keys and estimation data as values
        """
        # Parse the markdown file
        feature_tree = MarkdownFeatureParser.parse_markdown_file(markdown_path)
        feature_dict = MarkdownFeatureParser.flatten_features(feature_tree)
        
        # Store all estimations
        all_estimates = {}
        
        # First pass: Estimate parent features
        for parent, children in feature_dict.items():
            print(f"\n\nEstimating parent feature: {parent}")
            parent_estimate = self.estimate_feature(parent, child_features=children)
            all_estimates[parent] = FeatureEstimate(
                feature=parent,
                estimate=parent_estimate,
                children=[]
            )
            
        # Second pass: Estimate child features
        for parent, children in feature_dict.items():
            for child in children:
                print(f"  Estimating child feature: {child}")
                child_estimate = self.estimate_feature(child, parent_feature=parent)
                child_feature_estimate = FeatureEstimate(
                    feature=child,
                    parent_feature=parent,
                    estimate=child_estimate
                )
                all_estimates[parent].children.append(child_feature_estimate)
            
        return all_estimates
    
    def generate_report(self, estimates: Dict[str, FeatureEstimate], output_dir: str = "estimates") -> str:
        """Generate a detailed report for the estimates"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"estimate_report_{timestamp}.md"
        report_path = os.path.join(output_dir, report_filename)
        
        with open(report_path, 'w') as f:
            f.write("# Feature Estimation Report\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            total_time_estimate = "0"  # Placeholder for total time
            
            for parent_title, parent_data in estimates.items():
                f.write(f"## {parent_title}\n\n")
                f.write(f"### Summary\n{parent_data.estimate.summary}\n\n")
                f.write(f"### Time Estimate\n{parent_data.estimate.total_estimate}\n\n")
                
                f.write("### Task Breakdown\n")
                for task in parent_data.estimate.task_breakdown:
                    f.write(f"- **{task.task_name}** ({task.difficulty}): {task.description}\n")
                    f.write(f"  - Estimate: {task.time_estimate}\n")
                f.write("\n")
                
                if parent_data.estimate.api_analysis:
                    f.write("### API Analysis\n")
                    for api in parent_data.estimate.api_analysis:
                        f.write(f"- {api.method} {api.endpoint}: {api.purpose}\n")
                    f.write("\n")
                
                if parent_data.estimate.risks_and_considerations:
                    f.write("### Risks and Considerations\n")
                    for risk in parent_data.estimate.risks_and_considerations:
                        f.write(f"- {risk}\n")
                    f.write("\n")
                
                if parent_data.children:
                    f.write("### Child Features\n\n")
                    for child in parent_data.children:
                        f.write(f"#### {child.feature}\n\n")
                        f.write(f"Summary: {child.estimate.summary}\n\n")
                        f.write(f"Time Estimate: {child.estimate.total_estimate}\n\n")
                        
                        f.write("Task Breakdown:\n")
                        for task in child.estimate.task_breakdown:
                            f.write(f"- {task.task_name} ({task.difficulty}): {task.time_estimate}\n")
                        f.write("\n")
                
                f.write("---\n\n")
        
        return report_path
