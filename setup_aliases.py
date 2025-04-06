import xml.etree.ElementTree as ET


def rename_and_hookup_aliases(file_path):
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all <ALID> elements and rename them sequentially
    alias_counter = 1
    alias_map = {}  # Map old alias names to new ones
    for alid in root.findall(".//ALID"):
        new_alias = f"Body{alias_counter}"
        alias_map[alid.text] = new_alias
        alid.text = new_alias
        alias_counter += 1

    # Find the <QSTA> elements and ensure all aliases are hooked up
    # Ensure all aliases are hooked up in <QSTA>
    qsta_parent = root.find(".//QUST")
    if qsta_parent is not None:
        # Remove existing <QSTA> elements
        for qsta in qsta_parent.findall("QSTA"):
            qsta_parent.remove(qsta)

        # Add a <QSTA> element for each <ALST> value
        for alst in root.findall(".//ALST"):
            alias_index = alst.text  # Use the <ALST> value as the alias index
            qsta = ET.SubElement(qsta_parent, "QSTA")
            struct = ET.SubElement(qsta, "struct")
            struct.set("alias", alias_index)
            struct.set("flags", "0x00000000")

    # Write the modified XML back to the file
    tree.write(file_path, encoding="UTF-8", xml_declaration=True)


# Path to the XML file
file_path = r"WhereAreTheBodies.esx"

# Run the function
rename_and_hookup_aliases(file_path)
