"""Prompts for the interior designer application."""

ROOM_ANALYSIS_PROMPT = """Analyze this room image and provide a detailed assessment.

User Preferences:
- Style preference: {style}
- Budget: {budget}
- Specific needs: {specific_needs}

Please analyze the room and provide your response as a JSON object with the following structure:
{{
    "room_type": "type of room (e.g., living room, bedroom, kitchen)",
    "current_style": "current design style of the room",
    "estimated_dimensions": "rough estimate of room size if possible",
    "existing_furniture": ["list", "of", "furniture", "items"],
    "lighting_assessment": "assessment of natural and artificial lighting",
    "color_palette": ["current", "color", "palette"],
    "strengths": ["positive", "aspects", "of", "the", "room"],
    "improvement_opportunities": ["areas", "that", "could", "be", "improved"]
}}

Be specific and actionable in your analysis. Focus on practical observations that can inform design recommendations.
"""

DESIGN_RECOMMENDATIONS_PROMPT = """Based on the room analysis below, provide detailed design recommendations.

Room Analysis:
{room_analysis}

User Preferences:
- Style preference: {style}
- Budget: {budget}
- Specific needs: {specific_needs}

Please provide 3-5 prioritized recommendations as a JSON array. Each recommendation should follow this structure:
{{
    "category": "furniture/lighting/colors/decor/layout/storage",
    "current_state": "what currently exists",
    "recommendation": "specific actionable recommendation",
    "priority": "high/medium/low",
    "estimated_cost": "cost range like '$100-300' or 'low/medium/high'",
    "product_suggestions": ["specific", "product", "suggestions"],
    "image_edit_prompt": "a detailed prompt for an AI image generator to visualize this change - describe exactly what should change in the room while keeping everything else the same"
}}

Focus on practical, achievable improvements that match the user's style and budget. For the image_edit_prompt, be very specific about what should change (e.g., "Replace the old brown leather couch with a modern gray L-shaped sectional sofa, keep all other furniture and room elements exactly the same").
"""

SUMMARY_PROMPT = """Based on the room analysis and recommendations below, write a brief executive summary (2-3 paragraphs) that:
1. Highlights the key strengths of the current space
2. Identifies the top 2-3 priorities for improvement
3. Provides an overall vision for the redesigned space

Room Analysis:
{room_analysis}

Recommendations:
{recommendations}

User Preferences:
- Style preference: {style}
- Budget: {budget}
- Specific needs: {specific_needs}

Write the summary in a warm, encouraging tone that helps the user feel excited about their design project.
"""
