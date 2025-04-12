"""Example usage of the enhanced esx_lib.py functionality"""

import sys

from esx_lib import (
    ESXTES4,  # Added missing import
    ESXElement,
    ESXParser,
    ESXPlugin,
    FormIDManager,
    QuestBuilder,
    decimal_to_hex,
    hex_to_decimal,
    validate_esl_compatibility,
    validate_quest_structure,
    write_plugin_to_xml,
)


def clone_element_example(plugin: ESXPlugin) -> None:
    """Example showing element deep copying functionality"""
    print("\n=== Element Deep Copy Example ===")

    # Find a quest
    quest_group = next((g for g in plugin.groups if g.label == "QUST"), None)
    if not quest_group or not quest_group.records:
        print("No quest records found for clone example")
        return

    original_quest = quest_group.records[0]

    # Clone the quest
    cloned_quest = original_quest.clone()

    # Modify the clone
    edid = cloned_quest.find("EDID")
    if edid:
        edid.text = f"{edid.text}_COPY"

    full = cloned_quest.find("FULL")
    if full:
        full.text = f"{full.text} - Copy"

    # Verify independence of objects
    original_edid = original_quest.find("EDID")
    print(f"Original EDID: {original_edid.text if original_edid else 'None'}")
    cloned_edid = cloned_quest.find("EDID")
    print(f"Cloned EDID: {cloned_edid.text if cloned_edid else 'None'}")

    # Add the cloned quest
    if cloned_quest.attrib.get("id"):
        # Change form ID to avoid conflicts
        form_id = hex_to_decimal(cloned_quest.attrib["id"])
        cloned_quest.attrib["id"] = f"{form_id + 1:08x}"

    quest_group.add_record(cloned_quest)
    print("Quest cloned successfully")


def form_id_management_example() -> None:
    """Example showing form ID management functionality"""
    print("\n=== Form ID Management Example ===")

    # Create a form ID manager for ESL-compatible plugin
    manager = FormIDManager(start_id=0x800, end_id=0xFFF)

    # Reserve some specific IDs
    print("Reserving specific IDs: 0x800, 0x801, 0xA00")
    quest_id = manager.reserve_id("0x800")
    player_ref = manager.reserve_id(0x801)  # Can also use integer
    special_id = manager.reserve_id("0xA00")

    print(f"Reserved IDs: 0x{quest_id:x}, 0x{player_ref:x}, 0x{special_id:x}")

    # Allocate range of IDs
    print("\nAllocating 10 consecutive IDs")
    id_range = manager.allocate_range(10)
    print(f"Allocated range: {[f'0x{id:x}' for id in id_range]}")

    # Allocate individual IDs
    print("\nAllocating individual IDs")
    ids = [manager.allocate_next_id() for _ in range(5)]
    print(f"Allocated IDs: {[f'0x{id:x}' for id in ids]}")

    # Check usage status
    print(f"\nTotal used IDs: {manager.get_used_count()}")
    print(f"Is 0x801 used? {manager.is_id_used('0x801')}")
    print(f"Is 0x802 used? {manager.is_id_used('0x802')}")

    # Check ESL compatibility
    print(f"Is 0x801 in ESL range? {manager.is_in_esl_range('0x801')}")
    print(f"Is 0x10000 in ESL range? {manager.is_in_esl_range('0x10000')}")

    try:
        # Try to reserve an already used ID
        manager.reserve_id(0x800)
    except Exception as e:
        print(f"\nExpected error: {str(e)}")


def quest_builder_example() -> None:
    """Example showing the QuestBuilder functionality"""
    print("\n=== Quest Builder Example ===")

    # Create a new plugin
    plugin = ESXPlugin(tag="plugin")

    # Add TES4 header
    tes4 = ESXTES4(tag="TES4")
    tes4.add_master("Skyrim.esm")
    plugin.add_tes4(tes4)

    # Create a quest builder
    builder = QuestBuilder(plugin, "ExampleQuest", "0x800")

    # Set quest name
    builder.set_quest_name("Example Quest")

    # Add player reference alias
    player_ref_id = builder.add_player_ref()
    print(f"Added player reference alias with ID: 0x{player_ref_id:x}")

    # Add objectives with targets
    for i in range(1, 4):
        print(f"\nAdding objective {i} with 5 targets")
        result = builder.add_objective_with_targets(
            index=i,
            name=f"Complete task {i}",
            target_count=5,
            target_base_name=f"Objective{i}",
        )

        print(f"  Created objective: {result['objective'].name}")
        print(f"  Target IDs: {[f'0x{id:x}' for id in result['target_ids']]}")
        print(f"  Target aliases: {[a.name for a in result['target_aliases']]}")

    # Update alias count in quest record
    builder.update_alias_count()

    # Get form ID usage summary
    summary = builder.get_form_id_summary()
    print("\nForm ID usage summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Validate the quest structure
    is_valid, errors = validate_quest_structure(builder.quest)
    print(f"\nQuest structure valid: {is_valid}")
    if not is_valid:
        for error in errors:
            print(f"  Error: {error}")

    # Check ESL compatibility
    result = validate_esl_compatibility(plugin)
    print(f"\nESL compatible: {result}")

    # Write the plugin to XML
    output_file = "example_quest.xml"
    write_plugin_to_xml(plugin, output_file, pretty=True)
    print(f"\nWrote example quest to {output_file}")


def element_creation_examples() -> None:
    """Example showing the element creation helpers"""
    print("\n=== Element Creation Examples ===")

    # Create a condition element
    condition = ESXElement.create_condition_element(
        alias_id=0x801, function_index=566, comparison_value=1.0
    )
    print("Created condition element:")
    for child in condition.elements:
        value = child.text or "None"
        print(f"  {child.tag}: {value}")

    # Create objective elements
    objective_elements = ESXElement.create_objective_elements(
        index=1, name="Find the treasure", flags=0
    )
    print("\nCreated objective elements:")
    for elem in objective_elements:
        print(f"  {elem.tag}: {elem.text}")

    # Create alias elements
    alias_elements = ESXElement.create_alias_elements(
        alias_id=0x802, name="Treasure01", flags="4242", is_player_ref=False
    )
    print("\nCreated alias elements:")
    for elem in alias_elements:
        print(f"  {elem.tag}: {elem.text or elem.attrib}")


def utility_functions_example() -> None:
    """Example showing utility functions"""
    print("\n=== Utility Functions Example ===")

    # Hex/decimal conversions
    hex_val = "0x800"
    dec_val = hex_to_decimal(hex_val)
    print(f"Hex {hex_val} to decimal: {dec_val}")
    print(f"Decimal {dec_val} back to hex: {decimal_to_hex(dec_val)}")
    print(f"Decimal {dec_val} to hex without prefix: {decimal_to_hex(dec_val, False)}")

    # Convert decimal string
    print(f"Decimal string '2048' to hex: {decimal_to_hex('2048')}")

    # Convert hex string without prefix
    print(f"Hex string without prefix '800' to decimal: {hex_to_decimal('800')}")


def main() -> None:
    """Main entry point"""
    if len(sys.argv) > 1:
        # If file provided, load it
        input_file = sys.argv[1]
        try:
            parser = ESXParser()
            plugin = parser.parse_file(input_file)
            print(f"Loaded plugin from {input_file}")

            # Run examples that need a loaded plugin
            clone_element_example(plugin)

        except Exception as e:
            print(f"Error loading plugin: {str(e)}")
            import traceback

            traceback.print_exc()

    # Run examples that don't need a loaded plugin
    form_id_management_example()
    quest_builder_example()
    element_creation_examples()
    utility_functions_example()


if __name__ == "__main__":
    main()
