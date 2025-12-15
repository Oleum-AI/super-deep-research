import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import hashlib
from datetime import datetime

from models import Provider, ProviderReport
from services.llm_providers import LLMProviderService


@dataclass
class MasterReportResult:
    """Result of master report generation with content and thinking separated"""
    content: str
    thinking: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        return {"content": self.content, "thinking": self.thinking}

@dataclass
class Section:
    """Represents a section of a research report"""
    title: str
    content: str
    level: int
    provider: Provider
    hash: str = ""
    
    def __post_init__(self):
        # Create a hash of the content for deduplication
        self.hash = hashlib.md5(self.content.strip().encode()).hexdigest()

class ReportMerger:
    """Intelligently merges multiple research reports into a cohesive master report"""
    
    def __init__(self, merge_provider: Provider = Provider.OPENAI):
        self.merge_provider = merge_provider
        self.llm_service = LLMProviderService()
    
    async def merge_reports(self, reports: List[ProviderReport]) -> MasterReportResult:
        """Merge multiple provider reports into a single comprehensive report
        
        Returns:
            MasterReportResult with content and thinking separated
        """
        
        # Parse all reports into sections
        all_sections = []
        for report in reports:
            if report.content:
                sections = self.parse_report_sections(report.content, report.provider)
                all_sections.extend(sections)
        
        # Group sections by topic similarity
        grouped_sections = self.group_similar_sections(all_sections)
        
        # Deduplicate and merge content
        merged_sections = await self.merge_section_groups(grouped_sections)
        
        # Generate the final merged report
        master_report_result = await self.generate_master_report(merged_sections, reports)
        
        return master_report_result
    
    def parse_report_sections(self, content: str, provider: Provider) -> List[Section]:
        """Parse markdown content into sections"""
        sections = []
        
        # Split by headers (# ## ### etc)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            header_match = re.match(header_pattern, line, re.MULTILINE)
            
            if header_match:
                # Save previous section if exists
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    if current_section.content:  # Only add non-empty sections
                        sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = Section(
                    title=title,
                    content="",
                    level=level,
                    provider=provider
                )
                current_content = []
            else:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            if current_section.content:
                sections.append(current_section)
        
        return sections
    
    def group_similar_sections(self, sections: List[Section]) -> Dict[str, List[Section]]:
        """Group sections by similar topics"""
        groups = defaultdict(list)
        
        # Simple grouping by normalized title
        for section in sections:
            # Normalize title for grouping
            normalized_title = self.normalize_title(section.title)
            groups[normalized_title].append(section)
        
        return dict(groups)
    
    def normalize_title(self, title: str) -> str:
        """Normalize section titles for comparison"""
        # Convert to lowercase and remove common words
        title = title.lower().strip()
        
        # Remove common prefixes/suffixes
        common_words = ['the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']
        words = title.split()
        filtered_words = [w for w in words if w not in common_words]
        
        # Join back and remove special characters
        normalized = ' '.join(filtered_words)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized.strip()
    
    async def merge_section_groups(self, grouped_sections: Dict[str, List[Section]]) -> List[Dict]:
        """Merge similar sections, removing duplicates and reconciling conflicts"""
        merged_sections = []
        
        for group_title, sections in grouped_sections.items():
            if len(sections) == 1:
                # Single section, no merging needed
                merged_sections.append({
                    "title": sections[0].title,
                    "content": sections[0].content,
                    "level": sections[0].level,
                    "sources": [sections[0].provider]
                })
            else:
                # Multiple sections need merging
                merged = await self.merge_similar_content(sections)
                merged_sections.append(merged)
        
        # Sort sections by a logical order
        merged_sections.sort(key=lambda x: (x['level'], x['title']))
        
        return merged_sections
    
    async def merge_similar_content(self, sections: List[Section]) -> Dict:
        """Merge similar content from multiple sources"""
        # Deduplicate exact matches
        unique_contents = {}
        for section in sections:
            if section.hash not in unique_contents:
                unique_contents[section.hash] = section
        
        # If all sections are identical, return one
        if len(unique_contents) == 1:
            section = list(unique_contents.values())[0]
            return {
                "title": section.title,
                "content": section.content,
                "level": section.level,
                "sources": [s.provider for s in sections]
            }
        
        # For different content, intelligently merge
        provider = self.llm_service.get_provider(self.merge_provider)
        if not provider:
            # Fallback: concatenate all unique content
            combined_content = "\n\n".join([
                f"**According to {s.provider.value}:**\n{s.content}"
                for s in unique_contents.values()
            ])
            return {
                "title": sections[0].title,
                "content": combined_content,
                "level": sections[0].level,
                "sources": [s.provider for s in sections]
            }
        
        # Use LLM to intelligently merge
        merge_prompt = f"""You are tasked with merging the following sections from different AI providers into a single, cohesive section. 
Please:
1. Identify and keep all unique information
2. Resolve any conflicting information by noting the different perspectives
3. Remove redundant information
4. Create a well-structured, unified section
5. Maintain factual accuracy and cite sources when there are disagreements
6. IMPORTANT: Preserve all inline citations [1], [2], etc. from the original sections
7. IMPORTANT: Keep track of all references for the final References section

Section Title: {sections[0].title}

"""
        for section in unique_contents.values():
            merge_prompt += f"\n---\nFrom {section.provider.value}:\n{section.content}\n"
        
        merge_prompt += "\n---\nPlease provide the merged section content (preserve all citations):"
        
        try:
            # Provider now returns Dict with content and thinking
            result = await provider.generate_research_report(
                topic=merge_prompt,
                max_tokens=2000,
                include_web_search=False
            )
            # Discard intermediate thinking, just use content
            merged_content = result.get("content", "") if isinstance(result, dict) else result
            
            return {
                "title": sections[0].title,
                "content": merged_content,
                "level": sections[0].level,
                "sources": [s.provider for s in sections]
            }
        except Exception as e:
            # Fallback on error
            combined_content = "\n\n".join([
                f"**{s.provider.value}:**\n{s.content}"
                for s in unique_contents.values()
            ])
            return {
                "title": sections[0].title,
                "content": combined_content,
                "level": sections[0].level,
                "sources": [s.provider for s in sections]
            }
    
    async def generate_master_report(self, merged_sections: List[Dict], original_reports: List[ProviderReport]) -> MasterReportResult:
        """Generate the final master report
        
        Returns:
            MasterReportResult with content and thinking separated
        """
        provider = self.llm_service.get_provider(self.merge_provider)
        
        if not provider:
            # Fallback: create a simple structured report
            return MasterReportResult(
                content=self.create_fallback_report(merged_sections, original_reports),
                thinking=None
            )
        
        # Create a summary of what we have
        section_summary = "\n".join([
            f"- {s['title']} (from {', '.join([p.value for p in s['sources']])})"
            for s in merged_sections
        ])
        
        # Generate executive summary and final report structure
        generation_prompt = f"""You are creating a master research report by synthesizing content from multiple AI providers.

You have the following merged sections available:
{section_summary}

Please create:
1. An executive summary that captures the key findings across all sources
2. A well-structured report that incorporates all the merged sections
3. A conclusion that synthesizes insights from all providers
4. Recommendations based on the collective analysis
5. IMPORTANT: Consolidate all citations and create a unified ## References section at the end
6. IMPORTANT: Renumber citations [1], [2], etc. to be consistent throughout the merged report

The merged sections content is provided below. Please integrate them into a cohesive, professional research report.

---
"""
        
        # Add merged sections content
        for section in merged_sections:
            generation_prompt += f"\n## {section['title']}\n{section['content']}\n"
        
        generation_prompt += "\n---\nPlease generate the complete master report with a unified References section:"
        
        try:
            # Provider now returns Dict with content and thinking
            result = await provider.generate_research_report(
                topic=generation_prompt,
                max_tokens=10000,
                include_web_search=False
            )
            
            # Extract content and thinking
            if isinstance(result, dict):
                master_content = result.get("content", "")
                master_thinking = result.get("thinking")
            else:
                master_content = result
                master_thinking = None
            
            # Add metadata footer to content
            master_content += self.create_metadata_footer(original_reports)
            
            return MasterReportResult(content=master_content, thinking=master_thinking)
            
        except Exception as e:
            # Fallback on error
            return MasterReportResult(
                content=self.create_fallback_report(merged_sections, original_reports),
                thinking=None
            )
    
    def create_fallback_report(self, merged_sections: List[Dict], original_reports: List[ProviderReport]) -> str:
        """Create a fallback report when LLM merging fails"""
        report = "# Master Research Report\n\n"
        report += "## Executive Summary\n\n"
        report += "This report synthesizes research from multiple AI providers to provide comprehensive insights.\n\n"
        
        # Add all merged sections
        for section in merged_sections:
            level_prefix = "#" * section['level']
            report += f"{level_prefix} {section['title']}\n\n"
            report += f"{section['content']}\n\n"
            report += f"*Sources: {', '.join([p.value for p in section['sources']])}*\n\n"
        
        # Add metadata
        report += self.create_metadata_footer(original_reports)
        
        return report
    
    def create_metadata_footer(self, original_reports: List[ProviderReport]) -> str:
        """Create metadata footer for the report"""
        footer = "\n\n---\n\n## Report Metadata\n\n"
        footer += "This master report was generated by merging research from the following providers:\n\n"
        
        for report in original_reports:
            word_count = len(report.content.split()) if report.content else 0
            footer += f"- **{report.provider.value}**: {word_count} words\n"
        
        footer += f"\nGenerated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        return footer
