"""Convert HTML content to clean Markdown format."""

import re
from html.parser import HTMLParser
from typing import List, Optional, Tuple


class HTMLToMarkdownConverter(HTMLParser):
    """Convert HTML to clean Markdown format."""
    
    def __init__(self):
        super().__init__()
        self.output = []
        self.current_tag = None
        self.list_stack = []  # Track nested lists
        self.link_href = None
        self.in_pre = False
        self.in_code = False
        self.skip_content = False
        self.style_tags = 0  # Track if we're inside style tags
        
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle opening HTML tags."""
        self.current_tag = tag
        attrs_dict = dict(attrs) if attrs else {}
        
        # Skip style and script content
        if tag in ["style", "script"]:
            self.skip_content = True
            self.style_tags += 1
            return
            
        if self.skip_content:
            return
            
        # Paragraphs
        if tag == "p":
            if self.output and self.output[-1] != "\n\n":
                self.output.append("\n\n")
                
        # Headers
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            if self.output and self.output[-1] != "\n\n":
                self.output.append("\n\n")
            self.output.append("#" * level + " ")
            
        # Bold/Strong
        elif tag in ["b", "strong"]:
            self.output.append("**")
            
        # Italic/Emphasis
        elif tag in ["i", "em"]:
            self.output.append("*")
            
        # Links
        elif tag == "a":
            self.link_href = attrs_dict.get("href", "")
            self.output.append("[")
            
        # Lists
        elif tag == "ul":
            self.list_stack.append("ul")
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
                
        elif tag == "ol":
            self.list_stack.append("ol")
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
                
        elif tag == "li":
            indent = "  " * (len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1] == "ul":
                self.output.append(f"{indent}- ")
            elif self.list_stack and self.list_stack[-1] == "ol":
                self.output.append(f"{indent}1. ")
                
        # Line breaks
        elif tag == "br":
            self.output.append("\n")
            
        # Horizontal rule
        elif tag == "hr":
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
            self.output.append("---\n")
            
        # Code
        elif tag == "code":
            self.in_code = True
            self.output.append("`")
            
        elif tag == "pre":
            self.in_pre = True
            if self.output and self.output[-1] != "\n\n":
                self.output.append("\n\n")
            self.output.append("```\n")
            
        # Blockquote
        elif tag == "blockquote":
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
            self.output.append("> ")
            
        # Table elements (basic support)
        elif tag == "table":
            if self.output and self.output[-1] != "\n\n":
                self.output.append("\n\n")
        elif tag == "tr":
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
        elif tag in ["td", "th"]:
            self.output.append("| ")
            
    def handle_endtag(self, tag: str):
        """Handle closing HTML tags."""
        # Handle style/script tags
        if tag in ["style", "script"]:
            self.style_tags = max(0, self.style_tags - 1)
            if self.style_tags == 0:
                self.skip_content = False
            return
            
        if self.skip_content:
            return
            
        # Bold/Strong
        if tag in ["b", "strong"]:
            self.output.append("**")
            
        # Italic/Emphasis
        elif tag in ["i", "em"]:
            self.output.append("*")
            
        # Links
        elif tag == "a":
            self.output.append(f"]({self.link_href})")
            self.link_href = None
            
        # Lists
        elif tag in ["ul", "ol"]:
            if self.list_stack:
                self.list_stack.pop()
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
                
        elif tag == "li":
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
                
        # Paragraphs and headers
        elif tag in ["p", "h1", "h2", "h3", "h4", "h5", "h6"]:
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
                
        # Code
        elif tag == "code":
            self.in_code = False
            self.output.append("`")
            
        elif tag == "pre":
            self.in_pre = False
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
            self.output.append("```\n")
            
        # Blockquote
        elif tag == "blockquote":
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
                
        # Table elements
        elif tag in ["td", "th"]:
            self.output.append(" ")
        elif tag == "tr":
            self.output.append("|")
            if self.output and self.output[-1] != "\n":
                self.output.append("\n")
                
    def handle_data(self, data: str):
        """Handle text content."""
        if self.skip_content:
            return
            
        # Clean up whitespace
        if not self.in_pre and not self.in_code:
            # Collapse multiple spaces
            data = re.sub(r'\s+', ' ', data)
            # Remove leading/trailing whitespace if we're at the start of a block
            if self.output and self.output[-1] in ["\n", "\n\n"]:
                data = data.lstrip()
                
        self.output.append(data)
        
    def get_markdown(self) -> str:
        """Get the converted markdown text."""
        result = "".join(self.output)
        
        # Clean up excessive newlines
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Clean up trailing whitespace
        result = "\n".join(line.rstrip() for line in result.split("\n"))
        
        return result.strip()


def html_to_markdown(html_content: str) -> str:
    """Convert HTML content to clean Markdown.
    
    Args:
        html_content: HTML string to convert
        
    Returns:
        Clean markdown text
    """
    if not html_content:
        return ""
        
    # Pre-process to handle common Teams meeting patterns
    html_content = preprocess_teams_html(html_content)
    
    converter = HTMLToMarkdownConverter()
    converter.feed(html_content)
    return converter.get_markdown()


def preprocess_teams_html(html: str) -> str:
    """Pre-process HTML to handle Teams-specific patterns.
    
    Args:
        html: Raw HTML content
        
    Returns:
        Cleaned HTML ready for conversion
    """
    # More targeted replacement of Teams meeting boilerplate
    # Only replace the specific div containing meeting join instructions
    html = re.sub(
        r'<p[^>]*>\s*<strong>\s*Join on your computer.*?</strong>\s*</p>',
        '<p><strong>Microsoft Teams meeting</strong></p>',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Remove only the Meeting ID line, not the entire div
    html = re.sub(
        r'<p[^>]*>\s*Meeting ID:[^<]*</p>',
        '',
        html,
        flags=re.IGNORECASE
    )
    
    # Remove passcode line
    html = re.sub(
        r'<p[^>]*>\s*Passcode:[^<]*</p>',
        '',
        html,
        flags=re.IGNORECASE
    )
    
    # Remove phone conference ID line
    html = re.sub(
        r'Phone Conference ID:[^<\n]*',
        '',
        html,
        flags=re.IGNORECASE
    )
    
    # Remove download teams / meeting options links
    html = re.sub(
        r'<div[^>]*>\s*<a[^>]*>Download Teams</a>.*?</div>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    return html


def extract_meeting_url(html_content: str) -> Optional[str]:
    """Extract meeting URL from HTML content.
    
    Args:
        html_content: HTML content that may contain meeting links
        
    Returns:
        Meeting URL if found, None otherwise
    """
    if not html_content:
        return None
        
    # Look for Teams meeting URLs
    teams_match = re.search(
        r'https://teams\.microsoft\.com/l/meetup-join/[^"\s<>]+',
        html_content
    )
    if teams_match:
        return teams_match.group(0)
        
    # Look for Zoom URLs
    zoom_match = re.search(
        r'https://[^\s]*zoom\.us/[^"\s<>]+',
        html_content
    )
    if zoom_match:
        return zoom_match.group(0)
        
    # Look for Google Meet URLs
    meet_match = re.search(
        r'https://meet\.google\.com/[^"\s<>]+',
        html_content
    )
    if meet_match:
        return meet_match.group(0)
        
    return None