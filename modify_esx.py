import sys
from typing import Optional

from esx_lib import (
    ESXCondition,
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


def modify_quest(quest: ESXQuest) -> None:
    """Apply modifications to a quest record"""
    print(f"Modifying quest: {quest.editor_id}")

    # Step 1: We're going to create a completely new quest with specific form IDs
    new_elements = []
    essential_tags = ["EDID", "VMAD", "DNAM", "NEXT", "INDX", "QSDT"]

    # Preserve essential elements (header, script data, etc.)
    for element in quest.elements:
        if element.tag in essential_tags:
            preserved_element = ESXElement(
                tag=element.tag,
                attrib=element.attrib.copy(),
                text=element.text,
            )
            for child in element.elements:
                child_copy = ESXElement(
                    tag=child.tag, attrib=child.attrib.copy(), text=child.text
                )
                for subchild in child.elements:
                    subchild_copy = ESXElement(
                        tag=subchild.tag,
                        attrib=subchild.attrib.copy(),
                        text=subchild.text,
                    )
                    child_copy.append(subchild_copy)
                preserved_element.append(child_copy)
            new_elements.append(preserved_element)

    # Update quest ID to 0x800 for ESL compatibility
    quest.attrib["id"] = "00000800"

    # Add FULL name element (quest name)
    full_element = ESXElement("FULL", text="Smart Markers")
    new_elements.append(full_element)

    # IMPORTANT: We need to reduce the number of aliases to fit within ESL limits
    # A maximum of 2048 form IDs are available (0x800-0xFFF)
    # We need 1 for quest + 1 for player ref + aliases
    max_aliases = 2046  # Max aliases we can have (2048 - 2)

    # Determine how many objectives and aliases per objective we can have
    # Let's aim for 20 objectives with 100 aliases each = 2000 total
    num_objectives = 20
    aliases_per_objective = 100
    total_aliases = num_objectives * aliases_per_objective + 1  # +1 for PlayerRef

    if total_aliases > max_aliases:
        print(
            f"Warning: Total aliases ({total_aliases}) exceeds ESL limit. Adjusting..."
        )
        # Reduce to fit within limits
        num_objectives = 20
        aliases_per_objective = (
            100  # 20*100 = 2000 aliases (+ quest + playerref = 2002 form IDs)
        )
        total_aliases = num_objectives * aliases_per_objective + 1

    # Dictionary to track allocated form IDs (to ensure uniqueness)
    used_form_ids = {"0x800", "0x801"}  # Quest and PlayerRef

    print(
        f"Creating {num_objectives} objectives with {aliases_per_objective} aliases each"
    )
    print(f"Total alias count: {total_aliases}")

    # Generate form IDs for all aliases - FIXED to use proper hex values
    alias_form_ids = []
    current_id = 0x802  # Start after PlayerRef

    for i in range(num_objectives * aliases_per_objective):
        # Ensure we stay within ESL limits
        if current_id > 0xFFF:
            print(
                f"Error: Form ID limit exceeded at alias {i + 1}. Max is 0xFFF (4095)."
            )
            # Reduce objective or alias count here if this happens
            break

        hex_id = f"0x{current_id:x}"
        # We'll store both hex string and decimal value for different uses
        alias_form_ids.append((hex_id, current_id))
        used_form_ids.add(hex_id)
        current_id += 1

    # Step 2: Add objectives elements
    for obj_index in range(1, num_objectives + 1):
        obj_num = ESXElement("QOBJ", text=str(obj_index))
        obj_flags = ESXElement("FNAM", text="0")
        obj_name = ESXElement("NNAM", text=f"Objective {obj_index}")
        new_elements.extend([obj_num, obj_flags, obj_name])

        # Create each objective's reference aliases and their target data
        for alias_index in range(1, aliases_per_objective + 1):
            global_alias_index = (obj_index - 1) * aliases_per_objective + alias_index

            # Verify we have enough form IDs allocated
            if global_alias_index > len(alias_form_ids):
                print(
                    f"Warning: Not enough form IDs for alias {obj_index}_{alias_index}"
                )
                continue

            form_id_hex, form_id_dec = alias_form_ids[global_alias_index - 1]

            # Add QSTA (target data) element for this alias
            qsta = ESXElement("QSTA")
            # Use the decimal form for struct attribute
            struct = ESXElement(
                "struct", {"alias": str(form_id_dec), "flags": "0x00000000"}
            )
            qsta.append(struct)
            new_elements.append(qsta)

            # Add CTDA condition element for this alias
            ctda = create_condition_element(form_id_dec)
            new_elements.append(ctda)

    # Step 3: Set the ANAM element with the total number of aliases
    new_elements.append(ESXElement("ANAM", text=str(total_aliases)))

    # Step 4: Add reference alias elements (ALST, ALID, etc.)
    for obj_index in range(1, num_objectives + 1):
        for alias_index in range(1, aliases_per_objective + 1):
            global_alias_index = (obj_index - 1) * aliases_per_objective + alias_index

            # Verify we have enough form IDs allocated
            if global_alias_index > len(alias_form_ids):
                continue

            form_id_hex, form_id_dec = alias_form_ids[global_alias_index - 1]

            alias_name = f"Objective{obj_index}_{alias_index}"

            # Use decimal for ALST
            alst = ESXElement("ALST", text=str(form_id_dec))
            alid = ESXElement("ALID", text=alias_name)
            fnam = ESXElement("FNAM", text="4242")
            vtck = ESXElement("VTCK", text="00000000")
            aled = ESXElement("ALED")

            new_elements.extend([alst, alid, fnam, vtck, aled])
            print(f"Added alias {form_id_hex} (dec: {form_id_dec}) as {alias_name}")

    # Step 5: Add PlayerRef alias
    player_ref_id = "801"  # decimal form of 0x801
    alst = ESXElement("ALST", text=player_ref_id)
    alid = ESXElement("ALID", text="PlayerRef")
    fnam = ESXElement("FNAM", text="0")
    alfr = ESXElement("ALFR", text="00000014")  # Player reference
    vtck = ESXElement("VTCK", text="00000000")
    aled = ESXElement("ALED")

    new_elements.extend([alst, alid, fnam, alfr, vtck, aled])
    print("Added PlayerRef alias (0x801)")

    # Step 6: Replace the quest's elements with our new elements
    quest.elements = new_elements

    # Step 7: Update objectives programmatically
    quest.objectives = []
    for obj_index in range(1, num_objectives + 1):
        objective = ESXObjective(obj_index, f"Objective {obj_index}", 0)

        # Add target for each reference alias in this objective
        for alias_index in range(1, aliases_per_objective + 1):
            global_alias_index = (obj_index - 1) * aliases_per_objective + alias_index

            # Verify we have enough form IDs allocated
            if global_alias_index > len(alias_form_ids):
                continue

            form_id_hex, form_id_dec = alias_form_ids[global_alias_index - 1]

            objective.add_target(
                form_id_dec, "0x00000000", [ESXCondition(function_index=566)]
            )

        quest.add_objective(objective)

    # Ensure version attribute exists on root plugin element
    root_element = quest
    while root_element.parent:
        root_element = root_element.parent
    if hasattr(root_element, "attrib") and isinstance(root_element, ESXPlugin):
        if "version" not in root_element.attrib:
            root_element.attrib["version"] = "0.7.4"

    # Summarize form ID usage
    print("\nForm ID allocation summary:")
    print("- Quest ID: 0x800")
    print("- PlayerRef ID: 0x801")
    print(f"- Alias form IDs: 0x802 to 0x{current_id - 1:x}")
    print(f"- Total unique form IDs: {len(used_form_ids)} (max allowed: 2048)")

    if current_id > 0xFFF:
        print("WARNING: Form IDs exceed the ESL limit of 0x800-0xFFF!")


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
