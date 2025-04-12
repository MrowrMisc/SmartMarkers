"""
Script to create a BethKit-compatible ESX file with multiple quests, each with one objective and multiple aliases.
This addresses the XML serialization issue where bethkit expects a specific format for CTDA elements.
"""

import sys
import xml.etree.ElementTree as ET


def create_multi_quest_esx(
    output_file: str, num_quests: int = 2, aliases_per_objective: int = 5
) -> None:
    """
    Creates an ESX file with multiple quests that is compatible with bethkit conversion.
    This uses direct XML manipulation to ensure proper format.

    Args:
        output_file: Path where the ESX file will be saved
        num_quests: Number of quests to create
        aliases_per_objective: Number of aliases per objective
    """
    # Start with base plugin structure
    root = ET.Element("plugin")

    # Add TES4 header
    tes4 = ET.SubElement(root, "TES4")
    ET.SubElement(tes4, "MAST").text = "Skyrim.esm"
    ET.SubElement(tes4, "DATA").text = "0"

    # Create QUST group
    qust_group = ET.SubElement(root, "GRUP", {"label": "QUST", "groupType": "0"})

    # Track form IDs
    next_form_id = 0x800

    # Create quests
    for q in range(1, num_quests + 1):
        quest_id = f"{next_form_id:08x}"
        next_form_id += 1

        quest = ET.SubElement(qust_group, "QUST", {"id": quest_id})

        # Basic quest info
        ET.SubElement(quest, "EDID").text = f"SM_MultiQuest_{q:02d}"
        ET.SubElement(quest, "FULL").text = f"MultiQuest {q}"

        # Player reference alias
        player_ref_id = next_form_id
        next_form_id += 1

        ET.SubElement(quest, "ALST").text = str(player_ref_id)
        ET.SubElement(quest, "ALID").text = "PlayerRef"
        ET.SubElement(quest, "FNAM").text = "0"
        ET.SubElement(quest, "ALFR").text = "00000014"
        ET.SubElement(quest, "VTCK").text = "00000000"
        ET.SubElement(quest, "ALED")

        # Quest objective
        ET.SubElement(quest, "QOBJ").text = "1"
        ET.SubElement(quest, "FNAM").text = "0"
        ET.SubElement(quest, "NNAM").text = f"Objective for MultiQuest {q}"

        # Create target aliases for this objective
        target_aliases = []
        for i in range(1, aliases_per_objective + 1):
            alias_id = next_form_id
            next_form_id += 1

            alias_name = f"Q{q}_Obj1_Target{i}"

            # Add alias elements
            ET.SubElement(quest, "ALST").text = str(alias_id)
            ET.SubElement(quest, "ALID").text = alias_name
            ET.SubElement(quest, "FNAM").text = "4242"
            ET.SubElement(quest, "VTCK").text = "00000000"
            ET.SubElement(quest, "ALED")

            # Add target data
            qsta = ET.SubElement(quest, "QSTA")
            ET.SubElement(
                qsta, "struct", {"alias": str(alias_id), "flags": "0x00000000"}
            )

            # Add condition with flat structure - THIS IS THE KEY DIFFERENCE
            ctda = ET.SubElement(quest, "CTDA")
            ET.SubElement(ctda, "operator").text = "0x00"
            ET.SubElement(ctda, "unknown0").text = "0x00,0x00,0x00"
            ET.SubElement(ctda, "comparisonValueFloat").text = "1.0"
            ET.SubElement(ctda, "functionIndex").text = "566"
            ET.SubElement(ctda, "padding").text = "0x00,0x00"
            ET.SubElement(ctda, "param1").text = f"0x{alias_id:08x}"
            ET.SubElement(ctda, "param2").text = "0x00000000"
            ET.SubElement(ctda, "runOnType").text = "0"
            ET.SubElement(ctda, "reference").text = "00000000"
            ET.SubElement(ctda, "unknown1").text = "0xffffffff"

            target_aliases.append(alias_name)

        # Add alias count
        ET.SubElement(quest, "ANAM").text = str(
            aliases_per_objective + 1
        )  # +1 for PlayerRef

        print(f"Created quest {q}: {aliases_per_objective} aliases")
        print(f"  First few aliases: {target_aliases[: min(5, len(target_aliases))]}")

    # Write the XML to file with XML declaration
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)

    total_form_ids = next_form_id - 0x800
    print(f"\nCreated {num_quests} quests with {aliases_per_objective} aliases each")
    print(f"Total form IDs used: {total_form_ids}")
    print(f"Output written to {output_file}")


def main():
    output_file = "CoolPlugin.esx"
    num_quests = 2
    aliases_per_objective = 5

    # Parse command line arguments
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    if len(sys.argv) > 2:
        num_quests = int(sys.argv[2])
    if len(sys.argv) > 3:
        aliases_per_objective = int(sys.argv[3])

    create_multi_quest_esx(output_file, num_quests, aliases_per_objective)


if __name__ == "__main__":
    main()
