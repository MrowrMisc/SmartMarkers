"""Script to create an ESX file with multiple quests, each with one objective and multiple aliases"""

import sys

from esx_lib import (
    ESXTES4,
    # ESXAlias, # No longer needed for manual creation
    ESXElement,
    # ESXObjective, # No longer needed for manual creation
    ESXPlugin,
    ESXQuest,
    FormIDManager,
    validate_esl_compatibility,
    write_plugin_to_xml,
)

# --- Configuration Constants ---

# Type 1: Miscellaneous Quests (Single Objective)
MISC_QUEST_COUNT = 20
MISC_OBJECTIVES_PER_QUEST = 1
MISC_ALIASES_PER_OBJECTIVE = 30
MISC_QUEST_TYPE = 6
MISC_QUEST_EDITOR_ID_FORMAT = "MP_SmartMarkers_Misc_{quest_idx:02d}"
MISC_QUEST_FULL_NAME_FORMAT = "Smart Markers Misc {quest_idx}"
MISC_OBJECTIVE_NAME_FORMAT = "Misc Objective {objective_index}"
MISC_ALIAS_NAME_FORMAT = "Obj{objective_index}_Ref{target_idx}"

# Type 2: Regular Quests (Single Objective)
REG_SINGLE_QUEST_COUNT = 4
REG_SINGLE_OBJECTIVES_PER_QUEST = 1
REG_SINGLE_ALIASES_PER_OBJECTIVE = 15
REG_SINGLE_QUEST_TYPE = 0
REG_SINGLE_QUEST_EDITOR_ID_FORMAT = "MP_SmartMarkers_Regular_Single_{quest_idx:02d}"
REG_SINGLE_QUEST_FULL_NAME_FORMAT = "Smart Markers Regular Single {quest_idx}"
REG_SINGLE_OBJECTIVE_NAME_FORMAT = "Reg Single Objective {objective_index}"
REG_SINGLE_ALIAS_NAME_FORMAT = "Obj{objective_index}_Ref{target_idx}"

# Type 3: Regular Quests (Multiple Objectives)
REG_MULTI_QUEST_COUNT = 4
REG_MULTI_OBJECTIVES_PER_QUEST = 15
REG_MULTI_ALIASES_PER_OBJECTIVE = 15
REG_MULTI_QUEST_TYPE = 0
REG_MULTI_QUEST_EDITOR_ID_FORMAT = "MP_SmartMarkers_Regular_Multiple_{quest_idx:02d}"
REG_MULTI_QUEST_FULL_NAME_FORMAT = "Smart Markers Regular Multi {quest_idx}"
REG_MULTI_OBJECTIVE_NAME_FORMAT = "Reg Multi Objective {objective_index}"
# Corrected alias name format to include objective_index consistently
REG_MULTI_ALIAS_NAME_FORMAT = "Obj{objective_index}_Ref{target_idx}"


def create_multi_quest_plugin(
    output_file: str,
    pretty_output: bool = False,  # Keep False for compatibility
) -> bool:
    """
    Create an ESX plugin file with multiple quests based on defined constants.

    Args:
        output_file: Path to output ESX file
        pretty_output: Whether to format XML output with indentation (default: False)

    Returns:
        bool: Success status
    """
    # Calculate total requirements for ESL check
    total_quests = MISC_QUEST_COUNT + REG_SINGLE_QUEST_COUNT + REG_MULTI_QUEST_COUNT
    total_misc_aliases = MISC_QUEST_COUNT * (
        1 + MISC_OBJECTIVES_PER_QUEST * MISC_ALIASES_PER_OBJECTIVE
    )  # +1 PlayerRef per quest
    total_reg_single_aliases = REG_SINGLE_QUEST_COUNT * (
        1 + REG_SINGLE_OBJECTIVES_PER_QUEST * REG_SINGLE_ALIASES_PER_OBJECTIVE
    )
    total_reg_multi_aliases = REG_MULTI_QUEST_COUNT * (
        1 + REG_MULTI_OBJECTIVES_PER_QUEST * REG_MULTI_ALIASES_PER_OBJECTIVE
    )
    total_aliases = (
        total_misc_aliases + total_reg_single_aliases + total_reg_multi_aliases
    )
    total_form_ids = total_quests + total_aliases

    # Check if we'll exceed ESL limits
    if total_form_ids > 2048:
        print(
            f"ERROR: Configuration would require {total_form_ids} form IDs, exceeding ESL limit of 2048"
        )
        # Suggest reducing counts if over limit
        print("Consider reducing counts in the configuration constants.")
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
    form_manager = FormIDManager(0x800, 0xFFF)  # ESL range 0x800-0xFFF

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

    # Track total aliases and quests for reporting
    total_alias_count = 0
    created_quests = []  # Store created quests to count later
    quest_global_index = 0  # To ensure unique quest indices for naming if needed

    # --- Loop 1: Miscellaneous Quests ---
    print("\n--- Creating Miscellaneous Quests ---")
    for i in range(MISC_QUEST_COUNT):
        quest_global_index += 1
        quest_idx = i + 1  # Index specific to this type
        quest, aliases_added = _create_quest_structure(
            form_manager,
            quest_idx,
            quest_global_index,
            MISC_QUEST_TYPE,
            MISC_OBJECTIVES_PER_QUEST,
            MISC_ALIASES_PER_OBJECTIVE,
            MISC_QUEST_EDITOR_ID_FORMAT,
            MISC_QUEST_FULL_NAME_FORMAT,
            MISC_OBJECTIVE_NAME_FORMAT,
            MISC_ALIAS_NAME_FORMAT,
        )
        quest_group.add_record(quest)
        created_quests.append(quest)
        total_alias_count += aliases_added

    # --- Loop 2: Regular Single-Objective Quests ---
    print("\n--- Creating Regular Single-Objective Quests ---")
    for i in range(REG_SINGLE_QUEST_COUNT):
        quest_global_index += 1
        quest_idx = i + 1  # Index specific to this type
        quest, aliases_added = _create_quest_structure(
            form_manager,
            quest_idx,
            quest_global_index,
            REG_SINGLE_QUEST_TYPE,
            REG_SINGLE_OBJECTIVES_PER_QUEST,
            REG_SINGLE_ALIASES_PER_OBJECTIVE,
            REG_SINGLE_QUEST_EDITOR_ID_FORMAT,
            REG_SINGLE_QUEST_FULL_NAME_FORMAT,
            REG_SINGLE_OBJECTIVE_NAME_FORMAT,
            REG_SINGLE_ALIAS_NAME_FORMAT,
        )
        quest_group.add_record(quest)
        created_quests.append(quest)
        total_alias_count += aliases_added

    # --- Loop 3: Regular Multi-Objective Quests ---
    print("\n--- Creating Regular Multi-Objective Quests ---")
    for i in range(REG_MULTI_QUEST_COUNT):  # This loops REG_MULTI_QUEST_COUNT (4) times
        quest_global_index += 1
        quest_idx = i + 1
        # _create_quest_structure is called exactly ONCE per loop iteration
        quest, aliases_added = _create_quest_structure(
            form_manager,
            quest_idx,
            quest_global_index,
            REG_MULTI_QUEST_TYPE,
            REG_MULTI_OBJECTIVES_PER_QUEST,
            REG_MULTI_ALIASES_PER_OBJECTIVE,
            REG_MULTI_QUEST_EDITOR_ID_FORMAT,
            REG_MULTI_QUEST_FULL_NAME_FORMAT,
            REG_MULTI_OBJECTIVE_NAME_FORMAT,
            REG_MULTI_ALIAS_NAME_FORMAT,
        )
        quest_group.add_record(quest)
        created_quests.append(quest)
        total_alias_count += aliases_added

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
    print(f"Total quests created: {len(created_quests)}")
    print(f"  - Misc (Type {MISC_QUEST_TYPE}): {MISC_QUEST_COUNT}")
    print(f"  - Reg Single (Type {REG_SINGLE_QUEST_TYPE}): {REG_SINGLE_QUEST_COUNT}")
    print(f"  - Reg Multi (Type {REG_MULTI_QUEST_TYPE}): {REG_MULTI_QUEST_COUNT}")
    print(f"Total aliases created: {total_alias_count}")
    print(f"Total form IDs used: {form_manager.get_used_count()}")
    print(f"ESL compatible: {is_compatible} (Used {form_count}/2048 FormIDs)")

    if not is_compatible:
        print("ESL compatibility errors:")
        for error in esl_errors:
            print(f"  - {error}")

    # Write the plugin to file
    write_plugin_to_xml(plugin, output_file, pretty=pretty_output)
    print(f"\nWrote multi-quest plugin to {output_file}")

    return True


def _create_quest_structure(
    form_manager: FormIDManager,
    quest_idx: int,
    quest_global_index: int,  # Use if unique naming across types is needed
    quest_type: int,
    objectives_per_quest: int,
    aliases_per_objective: int,
    quest_editor_id_format: str,
    quest_full_name_format: str,
    objective_name_format: str,
    alias_name_format: str,
) -> tuple[ESXQuest, int]:
    """Helper function to create a single quest with its objectives and aliases."""
    aliases_created_count = 0

    # Allocate quest form ID
    quest_form_id = form_manager.allocate_next_id()
    quest_form_id_hex = f"{quest_form_id:08x}"

    # Create quest editor ID and name using formats
    quest_name = quest_full_name_format.format(quest_idx=quest_idx)
    quest_editor_id = quest_editor_id_format.format(quest_idx=quest_idx)

    # These print statements are executed once at the start of the function call
    print(f"  Creating quest {quest_idx}: {quest_name} (Global: {quest_global_index})")
    print(f"    Form ID: 0x{quest_form_id:x}, Type: {quest_type}")

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
    # quest.editor_id = quest_editor_id # Not needed if EDID element is added manually

    # Add basic quest elements
    quest.append(ESXElement("EDID", text=quest_editor_id))
    quest.append(ESXElement("FULL", text=quest_name))

    # Add DNAM element for quest type with nested struct
    dnam = ESXElement("DNAM")
    dnam_struct_attrib = {
        "flags": "0x0111",
        "priority": "0",
        "unknown0": "0xff",
        "unknown1": "0x00000000",
        "type": str(quest_type),
    }
    dnam.append(ESXElement("struct", attrib=dnam_struct_attrib))  # Nest struct
    quest.append(dnam)  # Append parent DNAM

    # Add player reference alias manually
    player_ref_id = form_manager.allocate_next_id()
    quest.append(ESXElement("ALST", text=str(player_ref_id)))
    quest.append(ESXElement("ALID", text="PlayerRef"))
    quest.append(ESXElement("FNAM", text="0"))
    quest.append(ESXElement("ALFR", text="00000014"))  # Player reference FormID
    quest.append(ESXElement("VTCK", text="00000000"))
    quest.append(ESXElement("ALED"))  # Empty element often needed as a terminator
    aliases_created_count += 1

    total_quest_aliases_expected = 1  # Start with PlayerRef

    # Add objectives manually
    for obj_idx in range(1, objectives_per_quest + 1):
        objective_index = obj_idx
        objective_name = objective_name_format.format(
            # Removed quest_name from format string as it wasn't used
            objective_index=objective_index
        )

        # Add objective elements
        quest.append(ESXElement("QOBJ", text=str(objective_index)))
        quest.append(ESXElement("FNAM", text="0"))  # FNAM for QOBJ
        quest.append(ESXElement("NNAM", text=objective_name))

        total_quest_aliases_expected += aliases_per_objective

        # Add target aliases for this objective manually
        for target_idx in range(1, aliases_per_objective + 1):
            target_id = form_manager.allocate_next_id()
            # Use the passed alias_name_format, ensuring objective_index is available
            alias_name = alias_name_format.format(
                objective_index=objective_index,
                target_idx=target_idx,
                # quest_idx=quest_idx # Add if needed by format string
            )

            # Add alias elements
            quest.append(ESXElement("ALST", text=str(target_id)))
            quest.append(ESXElement("ALID", text=alias_name))
            quest.append(ESXElement("FNAM", text="4242"))  # FNAM for ALST
            quest.append(ESXElement("VTCK", text="00000000"))
            quest.append(ESXElement("ALED"))  # Terminator for alias definition

            # Add QSTA (target data) element with nested struct
            qsta = ESXElement("QSTA")
            qsta_struct_attrib = {"alias": str(target_id), "flags": "0x00000000"}
            qsta.append(ESXElement("struct", attrib=qsta_struct_attrib))  # Nest struct
            quest.append(qsta)  # Append parent QSTA

            # Add CTDA (condition) element with nested elements
            param1_hex = f"0x{target_id:08x}"  # Use correct alias FormID
            ctda = ESXElement("CTDA")
            ctda.append(ESXElement("operator", text="0x00"))
            ctda.append(ESXElement("unknown0", text="0x00,0x00,0x00"))
            ctda.append(ESXElement("comparisonValueFloat", text="1.0"))
            ctda.append(ESXElement("functionIndex", text="566"))  # GetIsAliasRef
            ctda.append(ESXElement("padding", text="0x00,0x00"))
            ctda.append(ESXElement("param1", text=param1_hex))  # Alias FormID
            ctda.append(ESXElement("param2", text="0x00000000"))
            ctda.append(ESXElement("runOnType", text="0"))  # Subject
            ctda.append(ESXElement("reference", text="00000000"))  # Invalid ref
            ctda.append(ESXElement("unknown1", text="0xffffffff"))
            quest.append(ctda)  # Append parent CTDA

            aliases_created_count += 1

    # Add alias count element (ANAM)
    quest.append(ESXElement("ANAM", text=str(total_quest_aliases_expected)))

    return quest, aliases_created_count


def main() -> None:
    """Main entry point"""
    output_file = "MultiQuestMarkers.esx"

    # Command line arguments are no longer used for counts, only output file
    if len(sys.argv) > 1:
        output_file = sys.argv[1]

    try:
        create_multi_quest_plugin(
            output_file=output_file,
            # Removed count arguments, using constants now
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
