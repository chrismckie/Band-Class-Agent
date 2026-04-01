import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from agent.planner import plan


def test_planner():
    """Run the planner against INSERT and SELECT prompts and print each result."""
    prompts = [
        # INSERT
        "Add Emma Rodriguez, a 10th grader, to the student list.",
        "Add a new trumpet to inventory with serial number TR-4821, condition is fair.",
        "Add these students: Jake Alvarez grade 11, Maria Chen grade 9, Devon Hill grade 12.",
        "Add the piece Commando March by Karl King, difficulty 3.",
        # DELETE
        "Remove Emma Rodriguez from the student list.",
        "Delete the piece Commando March from the music library.",
        # UPDATE
        "Change Emma Rodriguez's grade to 11.",
        "Mark trumpet TR-4821 as damaged.",
        "Update the difficulty of Commando March to 4.",
        # SELECT
        "Show me all students.",
        "Which students are in grade 11?",
        "How many trumpets do we have in good condition?",
        "Show me all pieces with difficulty 4.",
        "Which students play clarinet?",
        "What instruments are currently checked out?",
    ]
    for prompt in prompts:
        print(f"\n--- prompt: {prompt!r}")
        result = plan(prompt)
        print(f"    intent={result['intent']}, entity={result['entity']}, "
              f"filters={result['filters']}, records={result['records']}, "
              f"clarification={result['requires_clarification']}")


if __name__ == "__main__":
    test_planner()
