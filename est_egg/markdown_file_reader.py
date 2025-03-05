import os
import re
from typing import Dict, List, Optional

class MarkdownFileReader:
    """
    Utility class to read and parse markdown files containing software requirements.
    """
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        Read a markdown file and return its content as string.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Content of the file as string
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    @staticmethod
    def extract_sections(content: str) -> Dict[str, str]:
        """
        Extract sections from markdown content based on headings.
        
        Args:
            content: Markdown content
            
        Returns:
            Dictionary with heading titles as keys and section content as values
        """
        sections = {}
        current_section = "main"
        section_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('#'):
                if section_content:  # Save previous section
                    sections[current_section] = '\n'.join(section_content).strip()
                    section_content = []
                
                # Extract new section title (remove # characters and trim)
                current_section = re.sub(r'^#+\s*', '', line).strip()
            else:
                section_content.append(line)
        
        # Save the last section
        if section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections
    
    @staticmethod
    def extract_requirements(content: str) -> List[str]:
        """
        Extract requirements from markdown content by looking for specific patterns.
        
        Args:
            content: Markdown content
            
        Returns:
            List of requirement statements
        """
        requirements = []
        
        # Look for patterns that typically indicate requirements
        # 1. Items in lists (- [ ] Task or - Task)
        list_pattern = r'^\s*[-*]\s*(?:\[[x ]\])?\s*(.+)$'
        
        # 2. Lines in "Requirements" or similar sections
        
        lines = content.split('\n')
        for line in lines:
            list_match = re.match(list_pattern, line, re.MULTILINE)
            if list_match:
                requirements.append(list_match.group(1).strip())
        
        # Also extract sections that might contain requirements
        sections = MarkdownFileReader.extract_sections(content)
        for title, text in sections.items():
            if any(keyword in title.lower() for keyword in ['requirement', 'feature', 'user story', 'spec']):
                # Add section content if it's not already in requirements
                if text and text not in requirements:
                    requirements.append(text)
        
        return requirements
