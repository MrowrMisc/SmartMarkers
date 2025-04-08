import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class ESXElement:
    """Base class for all ESX elements"""

    tag: str
    attrib: dict[str, str] = field(default_factory=dict)
    text: Optional[str] = None
    elements: List["ESXElement"] = field(default_factory=list)
    parent: Optional["ESXElement"] = None

    def append(self, element: "ESXElement") -> None:
        element.parent = self
        self.elements.append(element)

    def to_xml(self) -> ET.Element:
        """Convert to XML element"""
        element = ET.Element(self.tag, self.attrib)
        if self.text:
            element.text = self.text

        for child in self.elements:
            element.append(child.to_xml())

        return element

    def find(self, tag: str) -> Optional["ESXElement"]:
        """Find first child element with matching tag"""
        return next((e for e in self.elements if e.tag == tag), None)

    def find_all(self, tag: str) -> List["ESXElement"]:
        """Find all child elements with matching tag"""
        return [e for e in self.elements if e.tag == tag]


@dataclass
class ESXPlugin(ESXElement):
    """Root plugin element"""

    version: str = "0.7.4"
    tes4: Optional["ESXTES4"] = None
    groups: List["ESXGroup"] = field(default_factory=list)

    def add_tes4(self, tes4: "ESXTES4") -> None:
        self.tes4 = tes4
        self.append(tes4)

    def add_group(self, group: "ESXGroup") -> None:
        self.groups.append(group)
        self.append(group)


@dataclass
class ESXRecord(ESXElement):
    """Base record class"""

    editor_id: Optional[str] = None

    def get_editor_id(self) -> Optional[str]:
        """Get the editor ID if present"""
        edid = self.find("EDID")
        return edid.text if edid else None


@dataclass
class ESXTES4(ESXRecord):
    """TES4 header record"""

    masters: List[str] = field(default_factory=list)

    def add_master(self, master_name: str) -> None:
        mast = ESXElement("MAST", text=master_name)
        data = ESXElement("DATA", text="0")
        self.append(mast)
        self.append(data)
        self.masters.append(master_name)


@dataclass
class ESXGroup(ESXElement):
    """GRUP element"""

    label: str = field(default="")
    group_type: str = field(default="")
    attrib: dict[str, str] = field(default_factory=dict)
    records: List[ESXRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.attrib.update({"label": self.label, "groupType": self.group_type})
        super().__init__("GRUP", self.attrib)

    def add_record(self, record: ESXRecord) -> None:
        self.records.append(record)
        self.append(record)


@dataclass
class ESXQuest(ESXRecord):
    """QUST record"""

    objectives: List["ESXObjective"] = field(default_factory=list)
    aliases: List["ESXAlias"] = field(default_factory=list)
    stages: List["ESXElement"] = field(default_factory=list)
    full_name: Optional[str] = None
    script: Optional[str] = None
    priority: Optional[int] = None
    quest_flags: Optional[str] = None

    def add_objective(self, objective: "ESXObjective") -> None:
        self.objectives.append(objective)

    def add_alias(self, alias: "ESXAlias") -> None:
        self.aliases.append(alias)

    def add_stage(self, stage: ESXElement) -> None:
        self.stages.append(stage)


@dataclass
class ESXObjective:
    """Quest objective representation"""

    index: int
    name: str
    flags: int = 0
    targets: List[dict[str, Union[int, str, List["ESXCondition"]]]] = field(
        default_factory=list
    )

    def add_target(
        self,
        alias_id: int,
        flags: int = 0,
        conditions: Optional[List["ESXCondition"]] = None,
    ) -> None:
        self.targets.append(
            {"alias": alias_id, "flags": flags, "conditions": conditions or []}
        )


@dataclass
class ESXAlias:
    """Quest alias representation"""

    index: int
    name: str
    flags: Optional[str] = None
    ref_id: Optional[str] = None
    conditions: List["ESXCondition"] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)


@dataclass
class ESXCondition:
    """CTDA condition"""

    operator: Optional[str] = None
    function_index: Optional[int] = None
    comparison_value: Optional[float] = None
    param1: Optional[str] = None
    param2: Optional[str] = None
    run_on_type: Optional[str] = None
    reference: Optional[str] = None


class ESXParser:
    """Parser to convert XML to ESX objects"""

    def __init__(self) -> None:
        self.current_quest: Optional[ESXQuest] = None
        self.current_objective: Optional[ESXObjective] = None

    def parse_file(self, filename: str) -> ESXPlugin:
        """Parse an ESX file and return a structured representation"""
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            return self.parse_plugin(root)
        except Exception as e:
            print(f"Error parsing {filename}: {str(e)}")
            raise

    def parse_plugin(self, root: ET.Element) -> ESXPlugin:
        """Parse the plugin root element"""
        plugin = ESXPlugin(tag=root.tag, version=root.get("version", "0.7.4"))

        # Parse each direct child
        for child in root:
            if child.tag == "TES4":
                plugin.add_tes4(self.parse_tes4(child))
            elif child.tag == "GRUP":
                plugin.add_group(self.parse_grup(child))

        return plugin

    def parse_tes4(self, element: ET.Element) -> ESXTES4:
        """Parse TES4 header"""
        tes4 = ESXTES4(tag=element.tag, attrib=element.attrib)

        for child in element:
            child_elem = ESXElement(tag=child.tag, attrib=child.attrib, text=child.text)

            # Parse struct elements
            if child.tag == "HEDR" and len(child) > 0:
                for struct_child in child:
                    if struct_child.tag == "struct":
                        struct_elem = ESXElement(
                            tag="struct", attrib=struct_child.attrib
                        )
                        child_elem.append(struct_elem)

            tes4.append(child_elem)

            # Track masters
            if child.tag == "MAST":
                tes4.masters.append(child.text)

        return tes4

    def parse_grup(self, element: ET.Element) -> ESXGroup:
        """Parse a GRUP element"""
        group = ESXGroup(
            tag=element.tag,
            label=element.get("label", ""),
            group_type=element.get("groupType", ""),
            attrib=element.attrib,
        )

        # Parse records in this group
        for child in element:
            if child.tag == "QUST":
                quest = self.parse_quest(child)
                group.add_record(quest)
            else:
                # Handle other record types if needed
                record = ESXRecord(tag=child.tag, attrib=child.attrib)
                self.parse_generic_elements(child, record)
                group.add_record(record)

        return group

    def parse_quest(self, element: ET.Element) -> ESXQuest:
        """Parse a QUST record"""
        quest = ESXQuest(tag=element.tag, attrib=element.attrib)
        self.current_quest = quest

        # Track the current objective and alias for relationship building
        current_objective = None
        current_alias = None
        conditions = []

        # First pass - create the basic structure
        for child in element:
            child_elem = ESXElement(tag=child.tag, attrib=child.attrib, text=child.text)
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

        # Second pass - handle aliases explicitly
        alias_data = {}  # To store alias information keyed by index
        current_alias_id = None

        # Find all aliases in the XML
        for child in element:
            if child.tag == "ALST":
                current_alias_id = child.text
                if current_alias_id not in alias_data:
                    alias_data[current_alias_id] = {"index": current_alias_id}
            elif child.tag == "ALID" and current_alias_id:
                if current_alias_id in alias_data:
                    alias_data[current_alias_id]["name"] = child.text
            elif child.tag == "FNAM" and current_alias_id:
                if current_alias_id in alias_data:
                    alias_data[current_alias_id]["flags"] = child.text
            elif child.tag == "ALFR" and current_alias_id:
                if current_alias_id in alias_data:
                    alias_data[current_alias_id]["ref_id"] = child.text
            elif child.tag == "ALED":
                current_alias_id = None

        # Create aliases from the collected data
        print(f"Found {len(alias_data)} aliases in XML")
        for alias_id, data in alias_data.items():
            if "name" in data:  # Only create if we have a name
                alias = ESXAlias(
                    index=data["index"],
                    name=data["name"],
                    flags=data.get("flags"),
                    ref_id=data.get("ref_id"),
                )
                quest.add_alias(alias)

        # Third pass - handle quest objectives
        # Reset tracking variables
        current_objective = None
        conditions = []

        for child in element:
            if child.tag == "QOBJ":
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
                    index=current_objective["index"],
                    name=current_objective["name"],
                    flags=current_objective["flags"],
                )
                quest.add_objective(obj)
                self.current_objective = obj
            elif child.tag == "QSTA":
                # This is a target for the current objective
                if len(child) > 0 and self.current_objective:
                    for struct_elem in child:
                        if struct_elem.tag == "struct":
                            alias_id = struct_elem.get("alias", "0")
                            flags = int(struct_elem.get("flags", "0x00000000"), 16)
                            self.current_objective.add_target(
                                alias_id, flags, conditions.copy()
                            )
                # Reset conditions after adding to objective
                conditions = []
            elif child.tag == "CTDA":
                # Parse condition and add to the current list
                cond = self.parse_condition(child)
                conditions.append(cond)

        # Debug output
        print(
            f"Quest {quest.editor_id} has {len(quest.aliases)} aliases and {len(quest.objectives)} objectives"
        )
        for alias in quest.aliases:
            print(f"  - Alias: {alias.index} = {alias.name}")

        return quest

    def parse_vmad(
        self, element: ET.Element, parent: ESXQuest
    ) -> List[dict[str, Union[str, int]]]:
        """Parse script info from VMAD"""
        scripts = []

        for child in element:
            if child.tag == "script":
                script_name = child.get("name", "")
                status = child.get("status", "")
                scripts.append({"name": script_name, "status": status})
                parent.script = script_name

            elif child.tag == "fragments":
                for frag_child in child:
                    if frag_child.tag == "alias":
                        for alias_child in frag_child:
                            if alias_child.tag == "script":
                                script_name = alias_child.get("name", "")
                                status = alias_child.get("status", "")
                                obj_id = frag_child.get("object", "")
                                alias_scripts = {
                                    "name": script_name,
                                    "status": status,
                                    "object": obj_id,
                                }
                                scripts.append(alias_scripts)

        return scripts

    def parse_dnam(self, element: ET.Element, quest: ESXQuest) -> None:
        """Parse quest flags and priority"""
        for child in element:
            if child.tag == "struct":
                quest.quest_flags = child.get("flags", "")
                quest.priority = int(child.get("priority", 0))

    def parse_condition(self, element: ET.Element) -> ESXCondition:
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

    def parse_generic_elements(
        self, xml_element: ET.Element, esx_element: ESXElement
    ) -> None:
        """Parse any sub-elements generically"""
        for child in xml_element:
            child_elem = ESXElement(tag=child.tag, attrib=child.attrib, text=child.text)
            self.parse_generic_elements(child, child_elem)
            esx_element.append(child_elem)


def summarize_plugin(plugin: ESXPlugin) -> str:
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


def write_plugin_to_xml(plugin: ESXPlugin, output_file: str) -> None:
    """Write the plugin back to XML"""
    root = plugin.to_xml()
    tree = ET.ElementTree(root)
    # Add XML declaration
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)


def main() -> None:
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
