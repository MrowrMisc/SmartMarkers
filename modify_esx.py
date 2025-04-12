import sys
from typing import Optional

from esx_lib import (
    ESXParser,
    ESXPlugin,
    ESXQuest,
    FormIDManager,
    QuestBuilder,
    validate_esl_compatibility,
    write_plugin_to_xml,
)


def modify_esx_file(input_file: str, output_file: str) -> bool:
    """Apply the specified modifications to the ESX file"""
    parser = ESXParser()
    plugin = parser.parse_file(input_file)

    quest_record: Optional[ESXQuest] = None
    for group in plugin.groups:
        if group.label == "QUST":
            for record in group.records:
                if isinstance(record, ESXQuest):
                    quest_record = record
                    break

    if not quest_record:
        print("Error: No quest record found in the plugin")
        return False

    modify_quest_using_builder(plugin, quest_record)
    write_plugin_to_xml(plugin, output_file, pretty=True)
    return True


def modify_quest_using_builder(plugin: ESXPlugin, quest: ESXQuest) -> None:
    """Apply modifications to a quest record using the QuestBuilder"""
    print(f"Modifying quest: {quest.editor_id}")

    # Step 1: Set up form ID manager and preserve essential elements
    form_manager = FormIDManager(0x800, 0xFFF)
    quest_id = form_manager.reserve_id(0x800)

    # Create a new QuestBuilder instance
    builder = QuestBuilder(plugin, quest.editor_id or "SmartMarkersQuest", "00000800")

    # Set the quest name
    builder.set_quest_name("Smart Markers")

    # Add player reference alias
    player_ref_id = builder.add_player_ref()
    print(f"Added PlayerRef alias (0x{player_ref_id:x})")

    # Step 2: Calculate number of objectives and aliases per objective
    # Staying within ESL constraints
    max_aliases = 2046  # Max aliases we can have (2048 - 2)
    num_objectives = 20
    aliases_per_objective = 100
    total_aliases = num_objectives * aliases_per_objective + 1  # +1 for PlayerRef

    if total_aliases > max_aliases:
        print(
            f"Warning: Total aliases ({total_aliases}) exceeds ESL limit. Adjusting..."
        )
        num_objectives = 20
        aliases_per_objective = (
            100  # 20*100 = 2000 aliases (+ quest + playerref = 2002 form IDs)
        )
        total_aliases = num_objectives * aliases_per_objective + 1

    print(
        f"Creating {num_objectives} objectives with {aliases_per_objective} aliases each"
    )
    print(f"Total alias count: {total_aliases}")

    # Step 3: Use QuestBuilder to create objectives with targets
    for obj_index in range(1, num_objectives + 1):
        print(f"Adding objective {obj_index} with {aliases_per_objective} targets")
        result = builder.add_objective_with_targets(
            index=obj_index,
            name=f"Objective {obj_index}",
            target_count=aliases_per_objective,
            target_base_name=f"Objective{obj_index}",
        )

    # Step 4: Update alias count
    builder.update_alias_count()

    # Step 5: Get summary of form ID usage
    summary = builder.get_form_id_summary()

    print("\nForm ID allocation summary:")
    print(f"- Quest ID: {summary['quest_id']}")
    print(f"- PlayerRef ID: {summary['player_ref_id']}")
    print(f"- Total unique form IDs: {summary['total_used_ids']} (max allowed: 2048)")
    print(f"- Remaining form IDs: {summary['remaining_ids']}")

    # Check ESL compatibility
    is_compatible, form_count, errors = validate_esl_compatibility(plugin)
    if not is_compatible:
        print("\nWARNING: Plugin exceeds ESL compatibility requirements:")
        for error in errors:
            print(f"- {error}")
    else:
        print("\nPlugin is ESL compatible.")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python modify_esx.py <input_file> <output_file>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        if modify_esx_file(input_file, output_file):
            print(f"Successfully modified {input_file} and saved to {output_file}")
        else:
            print("Modification failed")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
