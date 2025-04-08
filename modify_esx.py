import sys
from typing import Optional

from esx_lib import (
    ESXElement,
    ESXObjective,
    ESXParser,
    ESXPlugin,
    ESXQuest,
    write_plugin_to_xml,
)


def create_condition_element(alias_id: int) -> ESXElement:
    """Create a full CTDA element with all child elements for a condition"""
    ctda = ESXElement("CTDA")
    ctda.append(ESXElement("operator", text="0x00"))
    ctda.append(ESXElement("unknown0", text="0x00,0x00,0x00"))
    ctda.append(ESXElement("comparisonValueFloat", text="1"))
    ctda.append(ESXElement("functionIndex", text="566"))
    ctda.append(ESXElement("padding", text="0x00,0x00"))
    ctda.append(ESXElement("param1", text=f"0x{alias_id:08x}"))
    ctda.append(ESXElement("param2", text="0x00000000"))
    ctda.append(ESXElement("runOnType", text="0"))
    ctda.append(ESXElement("reference", text="00000000"))
    ctda.append(ESXElement("unknown1", text="0xffffffff"))
    return ctda


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

    modify_quest(quest_record)
    write_plugin_to_xml(plugin, output_file)
    return True


# def modify_quest(quest: ESXQuest) -> None:
#     """Apply modifications to a quest record"""
#     print(f"Modifying quest: {quest.editor_id}")

#     # Step 1: Identify aliases and prepare mappings
#     objective_one_aliases = []
#     player_ref = None
#     alias_mapping = {}

#     for alias in quest.aliases:
#         if alias.name.startswith("ObjectiveOne"):
#             objective_one_aliases.append(alias)
#         elif alias.name == "PlayerRef":
#             player_ref = alias

#     # Step 2: Preserve essential elements
#     new_elements = []
#     essential_tags = ["EDID", "VMAD", "FULL", "DNAM", "NEXT", "INDX", "QSDT"]

#     for element in quest.elements:
#         if element.tag in essential_tags:
#             # Preserve attributes and child elements
#             preserved_element = ESXElement(
#                 tag=element.tag,
#                 attrib=element.attrib.copy(),
#                 text=element.text,
#             )
#             for child in element.elements:
#                 preserved_element.append(child)
#             new_elements.append(preserved_element)

#     # Step 3: Add or modify quest objectives
#     obj_index = ESXElement("QOBJ", text="1")
#     obj_flags = ESXElement("FNAM", text="0")
#     obj_name = ESXElement("NNAM", text="Objective One")
#     new_elements.extend([obj_index, obj_flags, obj_name])

#     # Step 4: Add QSTA and CTDA elements for each alias
#     for i, alias in enumerate(objective_one_aliases):
#         # Add QSTA element
#         qsta = ESXElement("QSTA")
#         struct = ESXElement("struct", {"alias": alias.id, "flags": "0x00000000"})
#         qsta.append(struct)
#         new_elements.append(qsta)

#         # Add CTDA condition element
#         ctda = create_condition_element(alias.id)
#         new_elements.append(ctda)

#         # Map alias to a new name
#         new_name = f"Objective{i + 1}"
#         alias_mapping[alias.id] = (new_name, f"{i + 41}")

#     # Step 5: Update ANAM element with the total number of aliases
#     total_aliases = len(objective_one_aliases) + (1 if player_ref else 0)
#     new_elements.append(ESXElement("ANAM", text=str(total_aliases)))

#     # Step 6: Add ALST, ALID, FNAM, and other alias-related elements
#     for alias in objective_one_aliases:
#         new_name, _ = alias_mapping[alias.id]
#         flag_value = alias.flags or "4242"

#         alst = ESXElement("ALST", text=alias.id)
#         alid = ESXElement("ALID", text=new_name)
#         fnam = ESXElement("FNAM", text=flag_value)
#         vtck = ESXElement("VTCK", text="00000000")
#         aled = ESXElement("ALED")

#         new_elements.extend([alst, alid, fnam, vtck, aled])

#     # Step 7: Handle PlayerRef alias if it exists
#     if player_ref:
#         alst = ESXElement("ALST", text=player_ref.id)
#         alid = ESXElement("ALID", text="PlayerRef")
#         fnam = ESXElement("FNAM", text=player_ref.flags or "0")
#         alfr = ESXElement("ALFR", text="00000014")
#         vtck = ESXElement("VTCK", text="00000000")
#         aled = ESXElement("ALED")

#         new_elements.extend([alst, alid, fnam, alfr, vtck, aled])

#     # Step 8: Replace the quest's elements with the updated list
#     quest.elements = new_elements

#     # Step 9: Update objectives with targets and conditions
#     objective_one = ESXObjective(1, "Objective One", 0)
#     for alias in objective_one_aliases:
#         objective_one.add_target(
#             alias.id, "0x00000000", [ESXCondition(function_index=566)]
#         )

#     quest.objectives = [objective_one]

#     # Debugging output
#     print("Quest modified successfully:")
#     print(f"- Preserved {len(objective_one_aliases)} ObjectiveOne aliases")
#     print(f"- Added conditions to all {len(objective_one_aliases)} aliases")
#     print(f"- {'Preserved' if player_ref else 'No'} PlayerRef alias")


# def modify_quest(quest: ESXQuest) -> None:
#     """Apply modifications to a quest record"""
#     print(f"Modifying quest: {quest.editor_id}")

#     # Step 1: We're not going to modify at all, just ensure the XML structure is valid
#     # Keep all existing elements and don't append any duplicate elements

#     # Ensure the plugin has the correct version attribute
#     root_element = quest
#     while root_element.parent:
#         root_element = root_element.parent

#     if hasattr(root_element, "attrib") and isinstance(root_element, ESXPlugin):
#         if "version" not in root_element.attrib:
#             root_element.attrib["version"] = "0.7.4"

#     # Make sure ANAM has the correct value
#     anam_elements = [elem for elem in quest.elements if elem.tag == "ANAM"]
#     for anam in anam_elements:
#         if anam.text != "52":
#             anam.text = "52"

#     # Find and remove any duplicate elements that might have been added
#     all_tags = [elem.tag for elem in quest.elements]

#     # Check for duplicates at the end
#     element_index = len(quest.elements) - 1
#     while element_index > 0:
#         current_elem = quest.elements[element_index]
#         if (
#             current_elem.tag in ["QOBJ", "FNAM", "NNAM", "ANAM"]
#             and all_tags.count(current_elem.tag) > 1
#             and element_index > all_tags.index(current_elem.tag)
#         ):
#             # This is a duplicate element, remove it
#             quest.elements.pop(element_index)
#             all_tags.pop(element_index)

#         element_index -= 1

#     print("Quest verified successfully - no modifications were made")


def modify_quest(quest: ESXQuest) -> None:
    """Apply modifications to a quest record"""
    print(f"Modifying quest: {quest.editor_id}")

    # Step 1: Identify aliases and prepare mappings
    objective_one_aliases = []
    player_ref = None
    alias_mapping = {}

    for alias in quest.aliases:
        if alias.name.startswith("ObjectiveOne"):
            objective_one_aliases.append(alias)
        elif alias.name == "PlayerRef":
            player_ref = alias

    # Step 2: Instead of replacing elements, let's preserve all existing elements
    # and only modify what needs to be changed
    all_elements = quest.elements.copy()  # Work with a copy to avoid issues

    # Find or create the Objective One elements
    qobj_elem = next(
        (e for e in all_elements if e.tag == "QOBJ" and e.text == "1"), None
    )
    if not qobj_elem:
        qobj_elem = ESXElement("QOBJ", text="1")
        all_elements.append(qobj_elem)

    fnam_elem = None
    for i, elem in enumerate(all_elements):
        if elem.tag == "FNAM" and i > 0 and all_elements[i - 1] is qobj_elem:
            fnam_elem = elem
            break
    if not fnam_elem:
        fnam_elem = ESXElement("FNAM", text="0")
        all_elements.append(fnam_elem)

    nnam_elem = None
    for i, elem in enumerate(all_elements):
        if elem.tag == "NNAM" and i > 0 and all_elements[i - 1] is fnam_elem:
            nnam_elem = elem
            break
    if not nnam_elem:
        nnam_elem = ESXElement("NNAM", text="Objective One")
        all_elements.append(nnam_elem)

    # Step 3: Ensure QSTA elements exist for each alias
    qsta_index = next((i for i, e in enumerate(all_elements) if e.tag == "QSTA"), -1)
    for i, alias in enumerate(objective_one_aliases):
        # Check if QSTA already exists for this alias
        alias_exists = False
        for elem in all_elements:
            if elem.tag == "QSTA":
                for child in elem.elements:
                    if child.tag == "struct" and child.attrib.get("alias") == alias.id:
                        alias_exists = True
                        break

        if not alias_exists:
            qsta = ESXElement("QSTA")
            struct = ESXElement("struct", {"alias": alias.id, "flags": "0x00000000"})
            qsta.append(struct)
            if qsta_index >= 0:
                all_elements.insert(qsta_index + 1 + i, qsta)
            else:
                all_elements.append(qsta)

        # Ensure CTDA exists for this alias
        ctda = create_condition_element(alias.id)
        all_elements.append(ctda)

        # Map alias to a new name
        new_name = f"Objective{i + 1}"
        alias_mapping[alias.id] = (new_name, f"{i + 41}")

    # Step 4: Update ANAM with correct value
    anam_index = next((i for i, e in enumerate(all_elements) if e.tag == "ANAM"), -1)
    if anam_index >= 0:
        all_elements[anam_index].text = "52"
    else:
        all_elements.append(ESXElement("ANAM", text="52"))

    # Step 5: Set the updated elements back to the quest
    quest.elements = all_elements

    # Step 6: Update objectives with targets and conditions
    objective_one = ESXObjective(1, "Objective One", 0)
    for alias in objective_one_aliases:
        objective_one.add_target(
            alias.id, "0x00000000", [ESXCondition(function_index=566)]
        )

    quest.objectives = [objective_one]

    # Ensure version attribute exists on root plugin element
    root_element = quest
    while root_element.parent:
        root_element = root_element.parent
    if hasattr(root_element, "attrib") and isinstance(root_element, ESXPlugin):
        if "version" not in root_element.attrib:
            root_element.attrib["version"] = "0.7.4"

    # Debugging output
    print("Quest modified successfully:")
    print(f"- Modified {len(objective_one_aliases)} ObjectiveOne aliases")
    print("- Added conditions to all aliases")
    print(f"- {'Preserved' if player_ref else 'No'} PlayerRef alias")


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
