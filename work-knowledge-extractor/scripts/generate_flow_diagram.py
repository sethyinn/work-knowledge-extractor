#!/usr/bin/env python3
"""
Generate Mermaid Flow Diagram for Work Knowledge Documentation

This script creates a Mermaid flowchart based on the extracted workflow stages.
It can handle:
- Simple linear workflows
- Decision-based workflows (with branches)
- Multi-role workflows (with role labels)
- Iterative workflows (with loops)

Usage:
    python generate_flow_diagram.py --stages <stages_data> --output <output_file>

Input format (JSON):
{
    "workflow_name": "Example Workflow",
    "workflow_type": "simple|decision|multi-role|iterative",
    "stages": [
        {
            "name": "Stage 1",
            "role": "Role A"  # optional, for multi-role workflows
        },
        {
            "name": "Stage 2",
            "role": "Role B"  # optional
        }
    ],
    "decisions": [  # optional, for decision-based workflows
        {
            "stage": "Stage 2",
            "name": "Decision 1",
            "options": [
                {"label": "Option A", "next_stage": "Stage 3A"},
                {"label": "Option B", "next_stage": "Stage 3B"}
            ]
        }
    ],
    "feedback_loops": [  # optional, for iterative workflows
        {"from": "Stage 3", "to": "Stage 2", "condition": "Changes needed"}
    ]
}

Output:
    Mermaid diagram code (saved to file or printed to stdout)
"""

import json
import sys
from pathlib import Path


def generate_simple_diagram(data):
    """Generate a simple linear flow diagram."""
    lines = ["graph TD"]

    # Add start node
    lines.append("    Start([Workflow Start]) --> S1[{}]".format(data['stages'][0]['name']))

    # Connect stages
    for i in range(len(data['stages']) - 1):
        current = data['stages'][i]
        next_stage = data['stages'][i + 1]
        lines.append("    S{}[{}] --> S{}[{}]".format(
            i + 1, current['name'], i + 2, next_stage['name']
        ))

    # Add end node
    lines.append("    S{} --> End([Workflow End])".format(len(data['stages'])))

    # Add styling
    lines.extend([
        "    style Start fill:#e1f5e1",
        "    style End fill:#ffe1e1"
    ])

    return '\n'.join(lines)


def generate_decision_diagram(data):
    """Generate a flow diagram with decision points."""
    lines = ["graph TD"]

    # Track all stage indices
    stage_indices = {}

    # Add start node
    lines.append("    Start([Workflow Start]) --> S1[{}]".format(data['stages'][0]['name']))
    stage_indices[data['stages'][0]['name']] = "S1"

    # Build the flow diagram with decisions
    current_index = 1
    stage_counter = 1

    for i, stage in enumerate(data['stages']):
        stage_key = stage['name']

        # Check if this stage has a decision
        decision = next((d for d in data.get('decisions', []) if d['stage'] == stage_key), None)

        if decision:
            # Add decision node
            decision_node = "D{}".format(current_index)
            lines.append("    S{} --> {}".format(stage_counter, decision_node))
            lines.append("    {}{{{}}}".format(decision_node, decision['name']))

            # Add decision options
            for opt_idx, option in enumerate(decision['options']):
                next_stage_name = option['next_stage']
                if next_stage_name not in stage_indices:
                    # This is a new stage
                    stage_counter += 1
                    stage_indices[next_stage_name] = "S{}".format(stage_counter)
                    lines.append("    {} -->|{}| {}[{}]".format(
                        decision_node, option['label'],
                        stage_indices[next_stage_name], next_stage_name
                    ))
                else:
                    # Connect to existing stage
                    lines.append("    {} -->|{}| {}".format(
                        decision_node, option['label'],
                        stage_indices[next_stage_name]
                    ))

            current_index += 1
        else:
            # No decision, connect to next stage
            if i < len(data['stages']) - 1:
                next_stage = data['stages'][i + 1]
                if next_stage['name'] not in stage_indices:
                    stage_counter += 1
                    stage_indices[next_stage['name']] = "S{}".format(stage_counter)
                    lines.append("    S{}[{}] --> {}[{}]".format(
                        stage_counter - 1, stage['name'],
                        stage_indices[next_stage['name']], next_stage['name']
                    ))

        stage_counter += 1

    # Connect all leaf nodes to End
    for stage_name, stage_id in stage_indices.items():
        # Check if this stage is a target of any connection
        is_target = any(stage_id in line for line in lines if '-->' in line and not line.startswith("    {}".format(stage_id)))
        # Don't add End node if it already connects to something
        if not any("{} -->".format(stage_id) in line for line in lines):
            lines.append("    {} --> End([Workflow End])".format(stage_id))

    # Add styling
    lines.extend([
        "    style Start fill:#e1f5e1",
        "    style End fill:#ffe1e1"
    ])

    # Style decision nodes
    for i in range(1, current_index + 1):
        lines.append("    style D{} fill:#fff4e1".format(i))

    return '\n'.join(lines)


def generate_multi_role_diagram(data):
    """Generate a flow diagram with role labels."""
    lines = ["graph TD"]

    # Add start node
    lines.append("    Start([Workflow Start]) --> S1[{}<br/>Owner: {}]".format(
        data['stages'][0]['name'],
        data['stages'][0].get('role', 'Unknown')
    ))

    # Connect stages with role labels
    for i in range(len(data['stages']) - 1):
        current = data['stages'][i]
        next_stage = data['stages'][i + 1]
        lines.append("    S{}[{}<br/>Owner: {}] --> S{}[{}<br/>Owner: {}]".format(
            i + 1, current['name'], current.get('role', 'Unknown'),
            i + 2, next_stage['name'], next_stage.get('role', 'Unknown')
        ))

    # Add end node
    lines.append("    S{} --> End([Complete])".format(len(data['stages'])))

    # Add styling for different roles
    roles = set(s.get('role', 'Unknown') for s in data['stages'])
    color_map = {
        'Role A': '#e3f2fd',
        'Role B': '#f3e5f5',
        'Role C': '#fff3e0',
        'Unknown': '#f5f5f5'
    }

    lines.extend([
        "    style Start fill:#e1f5e1",
        "    style End fill:#e8f5e9"
    ])

    for role in roles:
        color = color_map.get(role, '#f5f5f5')
        for i, stage in enumerate(data['stages']):
            if stage.get('role') == role:
                lines.append("    style S{} fill:{}".format(i + 1, color))

    return '\n'.join(lines)


def generate_iterative_diagram(data):
    """Generate a flow diagram with feedback loops."""
    lines = ["graph TD"]

    # Add stages
    for i, stage in enumerate(data['stages']):
        if i == 0:
            lines.append("    Start([Workflow Start]) --> S1[{}]".format(stage['name']))
        elif i < len(data['stages']) - 1:
            lines.append("    S{}[{}] --> S{}[{}]".format(i, stage['name'], i + 1, data['stages'][i]['name']))
        else:
            lines.append("    S{}[{}] --> End([Workflow End])".format(i, stage['name']))

    # Add feedback loops
    for loop in data.get('feedback_loops', []):
        from_stage = loop['from']
        to_stage = loop['to']
        condition = loop.get('condition', 'Iterate')

        # Find indices
        from_idx = next((i for i, s in enumerate(data['stages']) if s['name'] == from_stage), None)
        to_idx = next((i for i, s in enumerate(data['stages']) if s['name'] == to_stage), None)

        if from_idx and to_idx:
            lines.append("    S{} -->|{}| S{}".format(from_idx + 1, condition, to_idx + 1))

    # Add styling
    lines.extend([
        "    style Start fill:#e1f5e1",
        "    style End fill:#ffe1e1"
    ])

    return '\n'.join(lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python generate_flow_diagram.py --stages <json_file> --output <output_file>")
        print("\nExample:")
        print('  echo \'{"workflow_name":"Example","workflow_type":"simple","stages":[{"name":"Stage 1"},{"name":"Stage 2"}]}\' | python generate_flow_diagram.py --stages - --output diagram.mmd')
        sys.exit(1)

    # Parse arguments
    stages_arg = None
    output_file = None

    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '--stages' and i + 1 < len(sys.argv):
            stages_arg = sys.argv[i + 1]
        elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]

    if not stages_arg:
        print("Error: --stages argument is required")
        sys.exit(1)

    # Read input data
    if stages_arg == '-':
        # Read from stdin
        data = json.loads(sys.stdin.read())
    else:
        # Read from file
        with open(stages_arg, 'r', encoding='utf-8') as f:
            data = json.load(f)

    # Generate diagram based on workflow type
    workflow_type = data.get('workflow_type', 'simple')

    if workflow_type == 'simple':
        diagram = generate_simple_diagram(data)
    elif workflow_type == 'decision':
        diagram = generate_decision_diagram(data)
    elif workflow_type == 'multi-role':
        diagram = generate_multi_role_diagram(data)
    elif workflow_type == 'iterative':
        diagram = generate_iterative_diagram(data)
    else:
        print("Error: Unknown workflow type '{}'. Use 'simple', 'decision', 'multi-role', or 'iterative'.".format(workflow_type))
        sys.exit(1)

    # Output diagram
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(diagram, encoding='utf-8')
        print("✅ Diagram generated: {}".format(output_file))
    else:
        print(diagram)

    print("\n```mermaid")
    print(diagram)
    print("```")


if __name__ == "__main__":
    main()
