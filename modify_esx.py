import sys

from script import (
    ESXCondition,
    ESXElement,
    ESXObjective,
    ESXParser,
    write_plugin_to_xml,
)


def create_condition_element(alias_id):
    """Create a full CTDA element with all child elements for a condition"""
    ctda = ESXElement("CTDA")
    ctda.append(ESXElement("operator", text="0x00"))
    ctda.append(ESXElement("unknown0", text="0x00,0x00,0x00"))
    ctda.append(ESXElement("comparisonValueFloat", text="1"))
    ctda.append(ESXElement("functionIndex", text="566"))
    ctda.append(ESXElement("padding", text="0x00,0x00"))
    ctda.append(ESXElement("param1", text=f"0x{int(alias_id):08x}"))
    ctda.append(ESXElement("param2", text="0x00000000"))
    ctda.append(ESXElement("runOnType", text="0"))
    ctda.append(ESXElement("reference", text="00000000"))
    ctda.append(ESXElement("unknown1", text="0xffffffff"))
    return ctda


def modify_esx_file(input_file, output_file):
    """Apply the specified modifications to the ESX file"""
    parser = ESXParser()
    plugin = parser.parse_file(input_file)

    # Find the quest record
    quest_record = None
    for group in plugin.groups:
        if group.attrib.get("label") == "QUST":
            for record in group.records:
                if record.tag == "QUST":
                    quest_record = record
                    break

    if not quest_record:
        print("Error: No quest record found in the plugin")
        return False

    # Process the quest record
    modify_quest(quest_record)

    # Write the modified plugin back to file
    write_plugin_to_xml(plugin, output_file)
    return True


def modify_quest(quest):
    """Apply modifications to a quest record"""
    print(f"Modifying quest: {quest.editor_id}")

    # Find all reference aliases that start with ObjectiveOne
    objective_one_aliases = []
    player_ref_elem = None
    player_ref = None
    alias_mapping = {}  # To track original alias IDs

    # First pass: Identify all required aliases
    for element in quest.elements:
        if element.tag == "ALST":
            curr_alias_id = element.text
            curr_alias_name = None
            is_objective_one_alias = False
            is_player_ref = False

            # Look ahead for the ALID that follows this ALST
            idx = quest.elements.index(element)
            for i in range(idx + 1, min(idx + 5, len(quest.elements))):
                if quest.elements[i].tag == "ALID":
                    curr_alias_name = quest.elements[i].text
                    is_objective_one_alias = curr_alias_name.startswith("ObjectiveOne")
                    is_player_ref = curr_alias_name == "PlayerRef"
                    break

            if is_objective_one_alias:
                objective_one_aliases.append((curr_alias_id, curr_alias_name))
            elif is_player_ref:
                player_ref = curr_alias_id

    # Step 2: Build new elements list, preserving essential elements
    new_elements = []
    essential_tags = ["EDID", "VMAD", "FULL", "DNAM", "NEXT", "INDX", "QSDT"]

    # Add all essential elements
    for element in quest.elements:
        if element.tag in essential_tags:
            new_elements.append(element)

    # Add Objective One definition
    obj_index = ESXElement("QOBJ", text="1")
    obj_flags = ESXElement("FNAM", text="0")
    obj_name = ESXElement("NNAM", text="Objective One")
    new_elements.extend([obj_index, obj_flags, obj_name])

    # Add target data (QSTA) and conditions (CTDA) for each ObjectiveOne alias
    for i, (alias_id, alias_name) in enumerate(objective_one_aliases):
        # Create target data element
        qsta = ESXElement("QSTA")
        struct = ESXElement("struct", {"alias": alias_id, "flags": "0x00000000"})
        qsta.append(struct)
        new_elements.append(qsta)

        # Create condition element for this alias (all aliases now get conditions)
        ctda = create_condition_element(int(alias_id))
        new_elements.append(ctda)

        # Update alias mapping for renaming
        new_name = f"Objective{i + 1}"
        alias_mapping[alias_id] = (
            new_name,
            f"{i + 41}",
        )  # Store new name and potential new ID

    # Add ANAM (alias count)
    total_aliases = len(objective_one_aliases) + (1 if player_ref else 0)
    new_elements.append(ESXElement("ANAM", text=str(total_aliases)))

    # Add all renamed ObjectiveOne aliases
    for alias_id, original_name in objective_one_aliases:
        new_name, _ = alias_mapping[alias_id]

        # Find original alias elements to preserve flags
        flag_value = "4242"  # Default
        for i, elem in enumerate(quest.elements):
            if elem.tag == "ALST" and elem.text == alias_id:
                # Look for FNAM after this ALST
                for j in range(i + 1, min(i + 5, len(quest.elements))):
                    if quest.elements[j].tag == "FNAM":
                        flag_value = quest.elements[j].text
                        break
                break

        alst = ESXElement("ALST", text=alias_id)  # Keep original ID
        alid = ESXElement("ALID", text=new_name)  # Use new name
        fnam = ESXElement("FNAM", text=flag_value)
        vtck = ESXElement("VTCK", text="00000000")
        aled = ESXElement("ALED")

        new_elements.extend([alst, alid, fnam, vtck, aled])

    # Add PlayerRef if found
    if player_ref:
        # Find original PlayerRef elements
        for i, elem in enumerate(quest.elements):
            if elem.tag == "ALST" and elem.text == player_ref:
                alst = ESXElement("ALST", text=player_ref)
                alid = ESXElement("ALID", text="PlayerRef")

                # Look for FNAM, ALFR, and VTCK
                fnam = ESXElement("FNAM", text="0")  # Default
                alfr = ESXElement("ALFR", text="00000014")  # Default
                vtck = ESXElement("VTCK", text="00000000")  # Default

                for j in range(i + 1, min(i + 10, len(quest.elements))):
                    if quest.elements[j].tag == "FNAM":
                        fnam = ESXElement("FNAM", text=quest.elements[j].text)
                    elif quest.elements[j].tag == "ALFR":
                        alfr = ESXElement("ALFR", text=quest.elements[j].text)
                    elif quest.elements[j].tag == "VTCK":
                        vtck = ESXElement("VTCK", text=quest.elements[j].text)
                    elif quest.elements[j].tag == "ALED":
                        break

                aled = ESXElement("ALED")
                new_elements.extend([alst, alid, fnam, alfr, vtck, aled])
                break

    # Replace all elements with our new filtered list
    quest.elements = new_elements

    # Update quest's object model
    # This is mainly for the summary display
    objective_one = ESXObjective(1, "Objective One", 0)
    for alias_id, _ in objective_one_aliases:
        objective_one.add_target(
            alias_id, "0x00000000", [ESXCondition(function_index=566)]
        )

    quest.objectives = [objective_one]

    print("Quest modified successfully:")
    print(f"- Preserved {len(objective_one_aliases)} ObjectiveOne aliases")
    print(f"- Added conditions to all {len(objective_one_aliases)} aliases")
    print(f"- {'Preserved' if player_ref else 'No'} PlayerRef alias")

    return True


def main():
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
