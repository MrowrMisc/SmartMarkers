"""Script to create an ESX file with multiple quests, each with one objective and multiple aliases"""

import sys

from esx_lib import (
    ESXTES4,
    ESXAlias,
    ESXElement,
    ESXObjective,
    ESXPlugin,
    ESXQuest,
    FormIDManager,
    validate_esl_compatibility,
    write_plugin_to_xml,
)


def create_multi_quest_plugin(
    output_file: str,
    num_quests: int = 20,
    aliases_per_objective: int = 100,
    pretty_output: bool = False,  # Keep False for compatibility
) -> bool:
    """
    Create an ESX plugin file with multiple quests, each with one objective with multiple aliases

    Args:
        output_file: Path to output ESX file
        num_quests: Number of quests to create (default: 20)
        aliases_per_objective: Number of aliases per objective (default: 100)
        pretty_output: Whether to format XML output with indentation (default: False)

    Returns:
        bool: Success status
    """
    # Check if we'll exceed ESL limits
    total_aliases = num_quests * (aliases_per_objective + 1)  # +1 for PlayerRef
    total_form_ids = total_aliases + num_quests  # +1 for each quest

    if total_form_ids > 2048:
        print(
            f"ERROR: Configuration would require {total_form_ids} form IDs, exceeding ESL limit of 2048"
        )
        print(
            f"Consider reducing num_quests ({num_quests}) or aliases_per_objective ({aliases_per_objective})"
        )
        return False

    # Create the plugin with version attribute
    plugin = ESXPlugin(tag="plugin", attrib={"version": "0.7.4"})

    # Add TES4 header with attributes and required children
    tes4_attrib = {
        "flags": "0x00000000",
        "id": "00000000",
        "day": "0",
        "month": "0",
        "lastUserID": "0",
        "currentUserID": "0",
        "version": "44",
        "unknown": "0x0000",
    }
    tes4 = ESXTES4(tag="TES4", attrib=tes4_attrib)

    # HEDR will be added later with dynamic values
    tes4.append(ESXElement("CNAM", text="DEFAULT"))
    tes4.add_master("Skyrim.esm")  # This method adds MAST and DATA
    tes4.append(ESXElement("INTV", text="1"))
    plugin.add_tes4(tes4)  # Add TES4 early, HEDR will be inserted

    # Set up form ID manager
    form_manager = FormIDManager(0x800, 0xFFF)

    # Get a group for our quests with attributes
    grup_attrib = {
        "label": "QUST",
        "groupType": "0",
        "day": "0",
        "month": "0",
        "lastUserID": "0",
        "currentUserID": "0",
        "unknown": "0x00000000",
    }
    quest_group = plugin.get_or_create_group("QUST")
    quest_group.attrib.update(
        grup_attrib
    )  # Update attributes on the existing/created group

    # Track total aliases for reporting
    total_alias_count = 0
    created_quests = []  # Store created quests to count later

    # Create all quests manually instead of using QuestBuilder to ensure proper form ID handling
    for quest_idx in range(1, num_quests + 1):
        # Allocate quest form ID
        quest_form_id = form_manager.allocate_next_id()
        quest_form_id_hex = f"{quest_form_id:08x}"

        # Create quest editor ID and name
        quest_name = f"MultiQuest {quest_idx}"
        quest_editor_id = f"SM_MultiQuest_{quest_idx:02d}"

        print(f"\nCreating quest {quest_idx}/{num_quests}: {quest_name}")
        print(f"  Form ID: 0x{quest_form_id:x}")

        # Create quest record with attributes
        quest_attrib = {
            "id": quest_form_id_hex,
            "flags": "0x00000000",
            "day": "0",
            "month": "0",
            "lastUserID": "0",
            "currentUserID": "0",
            "version": "44",
            "unknown": "0x0000",
        }
        quest = ESXQuest(tag="QUST", attrib=quest_attrib)
        quest.editor_id = quest_editor_id  # Set editor_id property directly

        # Add basic quest elements
        quest.append(ESXElement("EDID", text=quest_editor_id))
        quest.append(ESXElement("FULL", text=quest_name))

        # Add quest to group
        quest_group.add_record(quest)
        created_quests.append(quest)

        # Add player reference alias
        player_ref_id = form_manager.allocate_next_id()
        print(f"  Added PlayerRef alias with form ID: 0x{player_ref_id:x}")

        # Create player ref alias elements
        quest.append(ESXElement("ALST", text=str(player_ref_id)))
        quest.append(ESXElement("ALID", text="PlayerRef"))
        quest.append(ESXElement("FNAM", text="0"))
        quest.append(ESXElement("ALFR", text="00000014"))  # Player reference
        quest.append(ESXElement("VTCK", text="00000000"))
        quest.append(ESXElement("ALED"))

        # Create an alias object and add it to quest
        player_alias = ESXAlias(
            index=player_ref_id, name="PlayerRef", flags="0", ref_id="00000014"
        )
        quest.add_alias(player_alias)
        total_alias_count += 1

        # Add one objective
        objective_index = 1
        objective_name = f"Objective for {quest_name}"
        print(
            f"  Adding objective {objective_index} with {aliases_per_objective} targets"
        )

        # Add objective elements
        quest.append(ESXElement("QOBJ", text=str(objective_index)))
        quest.append(ESXElement("FNAM", text="0"))  # FNAM for QOBJ
        quest.append(ESXElement("NNAM", text=objective_name))

        # Create objective object
        objective = ESXObjective(index=objective_index, name=objective_name)
        quest.add_objective(objective)

        # Track target IDs for reporting
        target_ids = []
        target_aliases = []

        # Add target aliases for this objective
        for target_idx in range(1, aliases_per_objective + 1):
            # Allocate a form ID for this target
            target_id = form_manager.allocate_next_id()
            target_ids.append(target_id)

            # Create alias name
            alias_name = f"Q{quest_idx}_Obj{objective_index}_Target{target_idx}"

            # Add alias elements
            quest.append(ESXElement("ALST", text=str(target_id)))
            quest.append(ESXElement("ALID", text=alias_name))
            quest.append(ESXElement("FNAM", text="4242"))  # FNAM for ALST
            quest.append(ESXElement("VTCK", text="00000000"))
            quest.append(ESXElement("ALED"))

            # Add QSTA (target data) element for this alias
            qsta = ESXElement("QSTA")
            struct = ESXElement(
                "struct", attrib={"alias": str(target_id), "flags": "0x00000000"}
            )
            qsta.append(struct)
            quest.append(qsta)

            # Revert CTDA creation to use nested elements
            param1_hex = f"0x{target_id:08x}"
            ctda = ESXElement("CTDA")
            ctda.append(ESXElement("operator", text="0x00"))
            ctda.append(ESXElement("unknown0", text="0x00,0x00,0x00"))
            ctda.append(ESXElement("comparisonValueFloat", text="1.0"))
            ctda.append(ESXElement("functionIndex", text="566"))
            ctda.append(ESXElement("padding", text="0x00,0x00"))
            ctda.append(ESXElement("param1", text=param1_hex))
            ctda.append(ESXElement("param2", text="0x00000000"))
            ctda.append(ESXElement("runOnType", text="0"))
            ctda.append(ESXElement("reference", text="00000000"))
            ctda.append(ESXElement("unknown1", text="0xffffffff"))
            quest.append(ctda)

            # Create alias object
            alias = ESXAlias(index=target_id, name=alias_name, flags="4242")
            quest.add_alias(alias)
            target_aliases.append(alias)
            total_alias_count += 1

        # Add alias count element
        total_quest_aliases = aliases_per_objective + 1  # +1 for PlayerRef
        quest.append(ESXElement("ANAM", text=str(total_quest_aliases)))

        # Report on created targets
        if target_ids:
            print(f"    Created objective: {objective.name}")
            print(f"    Target ID range: 0x{target_ids[0]:x} - 0x{target_ids[-1]:x}")
            print(f"    First few aliases: {[a.name for a in target_aliases[:5]]}")

    # Calculate next available object ID AFTER all allocations
    next_object_id_val = form_manager.allocate_next_id()
    # We don't actually want to use this ID, just get its value, so remove it
    form_manager.used_ids.remove(next_object_id_val)
    next_object_id_hex = f"{next_object_id_val:08x}"

    # Create and insert HEDR element into TES4
    hedr = ESXElement("HEDR")
    hedr_struct_attrib = {
        "version": "1.71000004",
        "numRecords": str(len(created_quests)),  # Use actual count of quests
        "nextObjectID": next_object_id_hex,
    }
    hedr.append(ESXElement("struct", attrib=hedr_struct_attrib))

    # Insert HEDR as the first element within TES4
    tes4.elements.insert(0, hedr)
    hedr.parent = tes4  # Set parent manually

    # Validate the plugin
    is_compatible, form_count, esl_errors = validate_esl_compatibility(plugin)

    print("\n=== Plugin Creation Summary ===")
    print(
        f"Created {num_quests} quests, each with 1 objective and {aliases_per_objective} aliases"
    )
    print(f"Total aliases created: {total_alias_count}")
    print(f"Total form IDs used: {form_manager.get_used_count()}")
    print(f"ESL compatible: {is_compatible}")

    if not is_compatible:
        print("ESL compatibility errors:")
        for error in esl_errors:
            print(f"  - {error}")

    # Write the plugin to file
    write_plugin_to_xml(plugin, output_file, pretty=pretty_output)
    print(f"\nWrote multi-quest plugin to {output_file}")

    return True


def main() -> None:
    """Main entry point"""
    output_file = "MultiQuestMarkers.esx"
    num_quests = 20
    aliases_per_objective = 100

    # For testing use smaller numbers
    # num_quests = 2
    # aliases_per_objective = 10

    # Override defaults if command line arguments are provided
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            num_quests = int(sys.argv[2])
        except ValueError:
            print(
                f"Invalid value for num_quests: {sys.argv[2]}. Using default: {num_quests}"
            )
    if len(sys.argv) > 3:
        try:
            aliases_per_objective = int(sys.argv[3])
        except ValueError:
            print(
                f"Invalid value for aliases_per_objective: {sys.argv[3]}. Using default: {aliases_per_objective}"
            )

    try:
        create_multi_quest_plugin(
            output_file=output_file,
            num_quests=num_quests,
            aliases_per_objective=aliases_per_objective,
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
