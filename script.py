import sys
import xml.etree.ElementTree as ET
from typing import Dict


# Base classes to handle XML element representation
class ESXElement:
    """Base class for all ESX elements"""

    def __init__(self, tag: str, attrib: Dict = None, text: str = None):
        self.tag = tag
        self.attrib = attrib or {}
        self.text = text
        self.elements = []  # Child elements in order
        self.parent = None

    def append(self, element):
        if isinstance(element, ESXElement):
            element.parent = self
        self.elements.append(element)

    def to_xml(self, parent=None):
        """Convert to XML element"""
        element = ET.Element(self.tag, self.attrib)
        if self.text:
            element.text = self.text

        for child in self.elements:
            if isinstance(child, ESXElement):
                child_elem = child.to_xml(element)
                element.append(child_elem)
            elif isinstance(child, ET.Element):
                element.append(child)

        return element

    def find(self, tag):
        """Find first child element with matching tag"""
        for element in self.elements:
            if isinstance(element, ESXElement) and element.tag == tag:
                return element
        return None

    def find_all(self, tag):
        """Find all child elements with matching tag"""
        return [e for e in self.elements if isinstance(e, ESXElement) and e.tag == tag]

    def __repr__(self):
        return f"{self.__class__.__name__}(tag='{self.tag}', attrib={self.attrib})"


class ESXPlugin(ESXElement):
    """Root plugin element"""

    def __init__(self, version: str = "0.7.4"):
        super().__init__("plugin", {"version": version})
        self.tes4 = None
        self.groups = []

    def add_tes4(self, tes4):
        self.tes4 = tes4
        self.append(tes4)

    def add_group(self, group):
        self.groups.append(group)
        self.append(group)


class ESXRecord(ESXElement):
    """Base record class"""

    def __init__(self, tag: str, attrib: Dict = None):
        super().__init__(tag, attrib)
        self.editor_id = None  # EDID value

    def get_editor_id(self):
        """Get the editor ID if present"""
        edid = self.find("EDID")
        return edid.text if edid and edid.text else None


class ESXTES4(ESXRecord):
    """TES4 header record"""

    def __init__(self, attrib: Dict = None):
        super().__init__("TES4", attrib)
        self.masters = []

    def add_master(self, master_name):
        mast = ESXElement("MAST", text=master_name)
        data = ESXElement("DATA", text="0")
        self.append(mast)
        self.append(data)
        self.masters.append(master_name)


class ESXGroup(ESXElement):
    """GRUP element"""

    def __init__(self, label: str, group_type: str, attrib: Dict = None):
        attrib = attrib or {}
        attrib["label"] = label
        attrib["groupType"] = group_type
        super().__init__("GRUP", attrib)
        self.records = []

    def add_record(self, record):
        self.records.append(record)
        self.append(record)


class ESXQuest(ESXRecord):
    """QUST record"""

    def __init__(self, attrib: Dict = None):
        super().__init__("QUST", attrib)
        self.objectives = []
        self.aliases = []
        self.stages = []
        self.full_name = None
        self.script = None
        self.priority = None
        self.quest_flags = None

    def add_objective(self, objective):
        self.objectives.append(objective)

    def add_alias(self, alias):
        self.aliases.append(alias)

    def add_stage(self, stage):
        self.stages.append(stage)


class ESXObjective:
    """Quest objective representation"""

    def __init__(self, index, name, flags=0):
        self.index = index
        self.name = name
        self.flags = flags
        self.targets = []  # List of target aliases and conditions

    def add_target(self, alias_id, flags=0, conditions=None):
        self.targets.append(
            {"alias": alias_id, "flags": flags, "conditions": conditions or []}
        )

    def __repr__(self):
        return f"Objective({self.index}, '{self.name}', {len(self.targets)} targets)"


class ESXAlias:
    """Quest alias representation"""

    def __init__(self, index, name, flags=None):
        self.index = index
        self.name = name
        self.flags = flags
        self.ref_id = None
        self.conditions = []
        self.scripts = []

    def __repr__(self):
        return f"Alias({self.index}, '{self.name}')"


class ESXCondition:
    """CTDA condition"""

    def __init__(
        self,
        operator=None,
        function_index=None,
        comparison_value=None,
        param1=None,
        param2=None,
        run_on_type=None,
        reference=None,
    ):
        self.operator = operator
        self.function_index = function_index
        self.comparison_value = comparison_value
        self.param1 = param1
        self.param2 = param2
        self.run_on_type = run_on_type
        self.reference = reference

    def __repr__(self):
        return f"Condition(func={self.function_index}, params=[{self.param1}, {self.param2}])"


class ESXParser:
    """Parser to convert XML to ESX objects"""

    def __init__(self):
        self.current_quest = None
        self.current_objective = None

    def parse_file(self, filename):
        """Parse an ESX file and return a structured representation"""
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            return self.parse_plugin(root)
        except Exception as e:
            print(f"Error parsing {filename}: {str(e)}")
            raise

    def parse_plugin(self, root):
        """Parse the plugin root element"""
        plugin = ESXPlugin(root.get("version", "0.7.4"))

        # Parse each direct child
        for child in root:
            if child.tag == "TES4":
                plugin.add_tes4(self.parse_tes4(child))
            elif child.tag == "GRUP":
                plugin.add_group(self.parse_grup(child))

        return plugin

    def parse_tes4(self, element):
        """Parse TES4 header"""
        tes4 = ESXTES4(element.attrib)

        for child in element:
            if isinstance(child.tag, str):
                child_elem = ESXElement(child.tag, child.attrib, child.text)

                # Parse struct elements
                if child.tag == "HEDR" and len(child) > 0:
                    for struct_child in child:
                        if struct_child.tag == "struct":
                            struct_elem = ESXElement("struct", struct_child.attrib)
                            child_elem.append(struct_elem)

                tes4.append(child_elem)

                # Track masters
                if child.tag == "MAST":
                    tes4.masters.append(child.text)

        return tes4

    def parse_grup(self, element):
        """Parse a GRUP element"""
        group = ESXGroup(element.get("label"), element.get("groupType"), element.attrib)

        # Parse records in this group
        for child in element:
            if child.tag == "QUST":
                quest = self.parse_quest(child)
                group.add_record(quest)
            else:
                # Handle other record types if needed
                record = ESXRecord(child.tag, child.attrib)
                self.parse_generic_elements(child, record)
                group.add_record(record)

        return group

    def parse_quest(self, element):
        """Parse a QUST record"""
        quest = ESXQuest(element.attrib)
        self.current_quest = quest

        # Track the current objective and alias for relationship building
        current_objective = None
        current_alias = None
        conditions = []

        # First pass - create the basic structure
        for child in element:
            child_elem = ESXElement(child.tag, child.attrib, child.text)
            self.parse_generic_elements(child, child_elem)
            quest.append(child_elem)

            # Extract quest metadata
            if child.tag == "EDID":
                quest.editor_id = child.text
            elif child.tag == "FULL":
                quest.full_name = child.text
            elif child.tag == "VMAD":
                self.parse_vmad(child, quest)
            elif child.tag == "DNAM":
                self.parse_dnam(child, quest)
            elif child.tag == "QOBJ":
                # Start tracking a new objective
                index = int(child.text) if child.text else 0
                current_objective = {
                    "index": index,
                    "flags": None,
                    "name": None,
                    "targets": [],
                }
                conditions = []  # Reset conditions for new objective
            elif child.tag == "FNAM" and current_objective:
                current_objective["flags"] = int(child.text) if child.text else 0
            elif child.tag == "NNAM" and current_objective:
                current_objective["name"] = child.text
                # At this point, we have enough to create an objective
                obj = ESXObjective(
                    current_objective["index"],
                    current_objective["name"],
                    current_objective["flags"],
                )
                quest.add_objective(obj)
                self.current_objective = obj
            elif child.tag == "QSTA":
                # This is a target for the current objective
                if len(child) > 0 and self.current_objective:
                    for struct_elem in child:
                        if struct_elem.tag == "struct":
                            alias_id = struct_elem.get("alias")
                            flags = struct_elem.get("flags", "0x00000000")
                            self.current_objective.add_target(
                                alias_id, flags, conditions.copy()
                            )
                # Reset conditions after adding to objective
                conditions = []
            elif child.tag == "CTDA":
                # Parse condition and add to the current list
                cond = self.parse_condition(child)
                conditions.append(cond)
            elif child.tag == "ALST":
                # Start tracking a new alias
                current_alias = {
                    "index": int(child.text) if child.text else 0,
                    "name": None,
                    "flags": None,
                }
            elif child.tag == "ALID" and current_alias:
                current_alias["name"] = child.text
            elif child.tag == "FNAM" and current_alias and current_alias.get("name"):
                current_alias["flags"] = child.text
                # At this point we can create the alias
                alias = ESXAlias(
                    current_alias["index"],
                    current_alias["name"],
                    current_alias["flags"],
                )
                quest.add_alias(alias)
                # Don't reset current_alias here as we might add more info to it
            elif child.tag == "ALFR" and current_alias:
                # Reference for alias
                ref = child.text
                for alias in quest.aliases:
                    if alias.index == current_alias["index"]:
                        alias.ref_id = ref
                        break
            elif child.tag == "ALED":
                # End of alias definition
                current_alias = None

        return quest

    def parse_vmad(self, element, parent):
        """Parse script info from VMAD"""
        scripts = []

        for child in element:
            if child.tag == "script":
                script_name = child.get("name")
                status = child.get("status")
                scripts.append({"name": script_name, "status": status})
                parent.script = script_name

            elif child.tag == "fragments":
                for frag_child in child:
                    if frag_child.tag == "alias":
                        for alias_child in frag_child:
                            if alias_child.tag == "script":
                                script_name = alias_child.get("name")
                                status = alias_child.get("status")
                                obj_id = frag_child.get("object")
                                alias_scripts = {
                                    "name": script_name,
                                    "status": status,
                                    "object": obj_id,
                                }
                                scripts.append(alias_scripts)

        return scripts

    def parse_dnam(self, element, quest):
        """Parse quest flags and priority"""
        for child in element:
            if child.tag == "struct":
                quest.quest_flags = child.get("flags")
                quest.priority = child.get("priority")

    def parse_condition(self, element):
        """Parse a CTDA condition"""
        cond = ESXCondition()

        for child in element:
            if child.tag == "operator":
                cond.operator = child.text
            elif child.tag == "comparisonValueFloat":
                cond.comparison_value = float(child.text) if child.text else None
            elif child.tag == "functionIndex":
                cond.function_index = int(child.text) if child.text else None
            elif child.tag == "param1":
                cond.param1 = child.text
            elif child.tag == "param2":
                cond.param2 = child.text
            elif child.tag == "runOnType":
                cond.run_on_type = child.text
            elif child.tag == "reference":
                cond.reference = child.text

        return cond

    def parse_generic_elements(self, xml_element, esx_element):
        """Parse any sub-elements generically"""
        for child in xml_element:
            child_elem = ESXElement(child.tag, child.attrib, child.text)
            self.parse_generic_elements(child, child_elem)
            esx_element.append(child_elem)


def summarize_plugin(plugin):
    """Generate a summary of the plugin's contents"""
    summary = []
    summary.append("# Skyrim ESP Plugin Summary\n")

    # TES4 Header
    if plugin.tes4:
        summary.append("## Plugin Header (TES4)\n")
        header_info = [f"- Version: {plugin.attrib.get('version', 'N/A')}"]

        # Get any HEDR/version info
        hedr = plugin.tes4.find("HEDR")
        if hedr:
            struct = hedr.find("struct")
            if struct:
                header_info.append(
                    f"- File Version: {struct.attrib.get('version', 'N/A')}"
                )
                header_info.append(
                    f"- Number of Records: {struct.attrib.get('numRecords', 'N/A')}"
                )
                header_info.append(
                    f"- Next Object ID: {struct.attrib.get('nextObjectID', 'N/A')}"
                )

        # Get creator info
        cnam = plugin.tes4.find("CNAM")
        if cnam and cnam.text:
            header_info.append(f"- Creator: {cnam.text}")

        # Get master files
        masters = plugin.tes4.find_all("MAST")
        if masters:
            header_info.append("- Master Files:")
            for master in masters:
                header_info.append(f"  - {master.text}")

        summary.append("\n".join(header_info))

    # Quest Groups
    for group in plugin.groups:
        if group.attrib.get("label") == "QUST":
            summary.append(f"\n## Quest Group ({len(group.records)} records)\n")

            for record in group.records:
                if not isinstance(record, ESXQuest):
                    continue  # Skip non-quest records

                quest = record
                summary.append(f"### Quest: {quest.full_name}\n")
                summary.append(f"- Editor ID: {quest.editor_id}")

                if quest.script:
                    summary.append(f"- Script: {quest.script}")

                if quest.quest_flags:
                    summary.append(f"- Flags: {quest.quest_flags}")

                if quest.priority:
                    summary.append(f"- Priority: {quest.priority}")

                # Objectives
                if quest.objectives:
                    summary.append("\n#### Objectives:\n")
                    for obj in quest.objectives:
                        target_info = []
                        for target in obj.targets:
                            alias_info = f"Alias {target['alias']}"
                            if target["conditions"]:
                                cond_strs = []
                                for cond in target["conditions"]:
                                    cond_str = f"Function {cond.function_index}"
                                    if cond.param1:
                                        cond_str += f" Param1={cond.param1}"
                                    if cond.param2:
                                        cond_str += f" Param2={cond.param2}"
                                    cond_strs.append(cond_str)
                                alias_info += (
                                    f" with conditions: [{', '.join(cond_strs)}]"
                                )
                            target_info.append(alias_info)

                        summary.append(f"- **{obj.index}: {obj.name}**")
                        if target_info:
                            summary.append(f"  - Targets: {', '.join(target_info)}")

                # Aliases
                if quest.aliases:
                    summary.append("\n#### Aliases:\n")
                    for alias in quest.aliases:
                        alias_info = [f"- **{alias.index}: {alias.name}**"]
                        if alias.flags:
                            alias_info.append(f"  - Flags: {alias.flags}")
                        if alias.ref_id:
                            alias_info.append(f"  - Reference: {alias.ref_id}")

                        summary.append("\n".join(alias_info))

                summary.append("\n")

    return "\n".join(summary)


def write_plugin_to_xml(plugin, output_file):
    """Write the plugin back to XML"""
    root = plugin.to_xml()
    tree = ET.ElementTree(root)
    # Add XML declaration
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python esx_parser.py <input_file> [output_file]")
        return

    input_file = sys.argv[1]

    try:
        parser = ESXParser()
        plugin = parser.parse_file(input_file)

        # Print summary
        summary = summarize_plugin(plugin)
        print(summary)

        # Write back to XML if output file provided
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
            write_plugin_to_xml(plugin, output_file)
            print(f"\nPlugin written to {output_file}")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
