from __future__ import annotations

import copy
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast


class ESXError(Exception):
    """Base class for all ESX-related exceptions"""

    pass


class ESXFormIDConflictError(ESXError):
    """Exception raised when there's a form ID conflict"""

    pass


class ESXInvalidElementError(ESXError):
    """Exception raised when an element structure is invalid"""

    pass


class ESXValidationError(ESXError):
    """Exception raised when validation fails"""

    pass


T = TypeVar("T", bound="ESXElement")


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

    def clone(self: T) -> T:
        """Create a deep copy of this element and its children"""
        # Create a new instance with same basic properties
        new_element = self.__class__(
            tag=self.tag, attrib=copy.deepcopy(self.attrib), text=self.text
        )

        # Copy all child elements recursively
        for child in self.elements:
            child_copy = child.clone()
            new_element.append(child_copy)

        return cast(T, new_element)

    @classmethod
    def create_condition_element(
        cls,
        alias_id: int,
        function_index: int = 566,
        comparison_value: float = 1.0,
        operator: str = "0x00",
        param2: str = "0x00000000",
        run_on_type: str = "0",
    ) -> "ESXElement":
        """Create a full CTDA element with all child elements for a condition"""
        ctda = cls("CTDA")
        ctda.append(cls("operator", text=operator))
        ctda.append(cls("unknown0", text="0x00,0x00,0x00"))
        ctda.append(cls("comparisonValueFloat", text=str(comparison_value)))
        ctda.append(cls("functionIndex", text=str(function_index)))
        ctda.append(cls("padding", text="0x00,0x00"))
        ctda.append(cls("param1", text=f"0x{alias_id:08x}"))
        ctda.append(cls("param2", text=param2))
        ctda.append(cls("runOnType", text=run_on_type))
        ctda.append(cls("reference", text="00000000"))
        ctda.append(cls("unknown1", text="0xffffffff"))
        return ctda

    @classmethod
    def create_objective_elements(
        cls, index: int, name: str, flags: int = 0
    ) -> List["ESXElement"]:
        """Create a set of elements for a quest objective"""
        obj_num = cls("QOBJ", text=str(index))
        obj_flags = cls("FNAM", text=str(flags))
        obj_name = cls("NNAM", text=name)
        return [obj_num, obj_flags, obj_name]

    @classmethod
    def create_alias_elements(
        cls, alias_id: int, name: str, flags: str = "0", is_player_ref: bool = False
    ) -> List["ESXElement"]:
        """Create a set of elements for a quest alias"""
        elements = []
        alst = cls("ALST", text=str(alias_id))
        alid = cls("ALID", text=name)
        fnam = cls("FNAM", text=flags)
        elements.extend([alst, alid, fnam])

        if is_player_ref:
            alfr = cls("ALFR", text="00000014")  # Player reference
            elements.append(alfr)

        vtck = cls("VTCK", text="00000000")
        aled = cls("ALED")
        elements.extend([vtck, aled])

        return elements


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

    def get_or_create_group(self, label: str, group_type: str = "0") -> "ESXGroup":
        """Get an existing group by label or create a new one"""
        for group in self.groups:
            if group.label == label:
                return group

        # Create new group
        group = ESXGroup(tag="GRUP", label=label, group_type=group_type)
        self.add_group(group)
        return group

    def get_quest(self, editor_id: str) -> Optional["ESXQuest"]:
        """Find a quest by editor ID"""
        for group in self.groups:
            if group.label == "QUST":
                for record in group.records:
                    if isinstance(record, ESXQuest) and record.editor_id == editor_id:
                        return record
        return None

    def get_or_create_quest(self, editor_id: str, form_id: str = None) -> "ESXQuest":
        """Get a quest by editor ID or create a new one"""
        existing_quest = self.get_quest(editor_id)
        if existing_quest:
            return existing_quest

        # Create new quest
        quest_group = self.get_or_create_group("QUST")
        attrib = {}
        if form_id:
            attrib["id"] = form_id

        quest = ESXQuest(tag="QUST", attrib=attrib)
        quest.editor_id = editor_id

        # Add EDID element
        edid_elem = ESXElement("EDID", text=editor_id)
        quest.append(edid_elem)

        quest_group.add_record(quest)
        return quest

    def is_esl_compatible(self) -> Tuple[bool, int, List[str]]:
        """Check if the plugin is compatible with ESL format

        Returns:
            Tuple of (is_compatible, form_id_count, error_messages)
        """
        form_ids = set()
        errors = []

        # Check all record form IDs
        for group in self.groups:
            for record in group.records:
                if "id" in record.attrib:
                    form_id = record.attrib["id"]

                    # Convert to int for comparison
                    try:
                        form_id_int = (
                            int(form_id, 16)
                            if form_id.startswith("0x")
                            else int(form_id, 16)
                        )

                        # Check if in ESL range (0x800-0xFFF)
                        if not (0x800 <= form_id_int <= 0xFFF):
                            errors.append(
                                f"Form ID {form_id} for {record.tag} is outside ESL range 0x800-0xFFF"
                            )

                        form_ids.add(form_id)
                    except ValueError:
                        errors.append(f"Invalid form ID format: {form_id}")

        is_compatible = len(errors) == 0 and len(form_ids) <= 2048
        if len(form_ids) > 2048:
            errors.append(
                f"Plugin uses {len(form_ids)} form IDs, which exceeds ESL limit of 2048"
            )

        return (is_compatible, len(form_ids), errors)


@dataclass
class ESXRecord(ESXElement):
    """Base record class"""

    editor_id: Optional[str] = None

    def get_editor_id(self) -> Optional[str]:
        """Get the editor ID if present"""
        edid = self.find("EDID")
        return edid.text if edid else None

    def set_editor_id(self, editor_id: str) -> None:
        """Set the editor ID"""
        edid = self.find("EDID")
        if edid:
            edid.text = editor_id
        else:
            edid = ESXElement("EDID", text=editor_id)
            self.append(edid)
        self.editor_id = editor_id


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

    def get_record(self, editor_id: str) -> Optional[ESXRecord]:
        """Find a record by editor ID"""
        for record in self.records:
            if record.get_editor_id() == editor_id:
                return record
        return None


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

    def get_objective(self, index: int) -> Optional["ESXObjective"]:
        """Get an objective by index"""
        for obj in self.objectives:
            if obj.index == index:
                return obj
        return None

    def get_or_create_objective(self, index: int, name: str) -> "ESXObjective":
        """Get an objective by index or create a new one"""
        obj = self.get_objective(index)
        if obj:
            return obj

        # Create new objective
        obj = ESXObjective(index=index, name=name)
        self.add_objective(obj)

        # Add element structure for this objective
        obj_elements = ESXElement.create_objective_elements(index, name)
        for elem in obj_elements:
            self.append(elem)

        return obj

    def set_full_name(self, full_name: str) -> None:
        """Set the quest's full name"""
        full_elem = self.find("FULL")
        if full_elem:
            full_elem.text = full_name
        else:
            full_elem = ESXElement("FULL", text=full_name)
            self.append(full_elem)
        self.full_name = full_name

    def add_condition_to_objective(
        self, obj_index: int, condition: "ESXCondition"
    ) -> None:
        """Add a condition to an objective"""
        obj = self.get_objective(obj_index)
        if not obj:
            raise ESXInvalidElementError(f"Objective {obj_index} not found")

        # Add the CTDA element to the quest structure
        ctda = ESXElement.create_condition_element(
            alias_id=int(condition.param1) if condition.param1 is not None else 0,
            function_index=condition.function_index
            if condition.function_index is not None
            else 0,
            comparison_value=condition.comparison_value or 1.0,
            operator=condition.operator or "0x00",
            param2=condition.param2 or "0x00000000",
            run_on_type=condition.run_on_type or "0",
        )
        self.append(ctda)

        # Update objective's conditions
        for target in obj.targets:
            target["conditions"].append(condition)


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
    param1: Optional[Union[int, str]] = None
    param2: Optional[str] = None
    run_on_type: Optional[str] = None
    reference: Optional[str] = None


class FormIDManager:
    """Manager for allocating and tracking form IDs"""

    def __init__(self, start_id: int = 0x800, end_id: int = 0xFFF):
        self.start_id = start_id
        self.end_id = end_id
        self.used_ids: Set[int] = set()

    def reserve_id(self, form_id: Union[int, str]) -> int:
        """Reserve a specific form ID"""
        # Convert string to int if needed
        form_id_int = self._to_int(form_id)

        if form_id_int < self.start_id or form_id_int > self.end_id:
            raise ESXFormIDConflictError(
                f"Form ID 0x{form_id_int:x} is outside valid range 0x{self.start_id:x}-0x{self.end_id:x}"
            )

        if form_id_int in self.used_ids:
            raise ESXFormIDConflictError(f"Form ID 0x{form_id_int:x} is already in use")

        self.used_ids.add(form_id_int)
        return form_id_int

    def allocate_next_id(self) -> int:
        """Allocate the next available ID"""
        next_id = self.start_id
        while next_id <= self.end_id:
            if next_id not in self.used_ids:
                self.used_ids.add(next_id)
                return next_id
            next_id += 1

        raise ESXFormIDConflictError("No more form IDs available in range")

    def allocate_range(self, count: int) -> List[int]:
        """Allocate a range of consecutive form IDs"""
        # Find a range of 'count' consecutive free IDs
        start_id = self.start_id

        while start_id + count - 1 <= self.end_id:
            # Check if this range is free
            range_free = True
            for i in range(count):
                if start_id + i in self.used_ids:
                    range_free = False
                    # Skip to after this used ID
                    start_id = start_id + i + 1
                    break

            if range_free:
                # Found a free range, allocate it
                allocated_ids = []
                for i in range(count):
                    self.used_ids.add(start_id + i)
                    allocated_ids.append(start_id + i)
                return allocated_ids

        raise ESXFormIDConflictError(f"Could not allocate {count} consecutive form IDs")

    def is_id_used(self, form_id: Union[int, str]) -> bool:
        """Check if a form ID is already used"""
        form_id_int = self._to_int(form_id)
        return form_id_int in self.used_ids

    def get_used_count(self) -> int:
        """Get the number of used form IDs"""
        return len(self.used_ids)

    def is_in_esl_range(self, form_id: Union[int, str]) -> bool:
        """Check if form ID is in ESL range (0x800-0xFFF)"""
        form_id_int = self._to_int(form_id)
        return 0x800 <= form_id_int <= 0xFFF

    def _to_int(self, form_id: Union[int, str]) -> int:
        """Convert form ID to integer"""
        if isinstance(form_id, int):
            return form_id

        # Handle hex strings (with or without 0x prefix)
        form_id_str = str(form_id).lower()
        if form_id_str.startswith("0x"):
            return int(form_id_str, 16)
        else:
            try:
                return int(form_id_str, 16)
            except ValueError:
                return int(form_id_str)


class QuestBuilder:
    """Helper class for constructing quests programmatically"""

    def __init__(
        self, plugin: ESXPlugin, editor_id: str, form_id: Optional[str] = None
    ):
        self.plugin = plugin
        self.form_id_manager = FormIDManager()

        # Reserve the quest form ID
        if form_id:
            self.quest_form_id = self.form_id_manager.reserve_id(form_id)
            form_id_str = f"{self.quest_form_id:08x}"
        else:
            self.quest_form_id = self.form_id_manager.allocate_next_id()
            form_id_str = f"{self.quest_form_id:08x}"

        # Create the quest or get existing one
        self.quest = plugin.get_or_create_quest(editor_id, form_id_str)

        # Track aliases and objectives
        self.aliases: Dict[int, ESXAlias] = {}
        self.player_ref_id = None

    def set_quest_name(self, name: str) -> "QuestBuilder":
        """Set the quest's full name"""
        self.quest.set_full_name(name)
        return self

    def add_player_ref(self) -> int:
        """Add player reference alias"""
        if self.player_ref_id is not None:
            return self.player_ref_id

        # Allocate ID after quest
        player_ref_id = self.form_id_manager.allocate_next_id()

        # Add player ref elements
        player_alias_elements = ESXElement.create_alias_elements(
            alias_id=player_ref_id, name="PlayerRef", flags="0", is_player_ref=True
        )

        for elem in player_alias_elements:
            self.quest.append(elem)

        # Add to quest aliases
        player_alias = ESXAlias(
            index=player_ref_id,
            name="PlayerRef",
            flags="0",
            ref_id="00000014",  # Player reference
        )
        self.quest.add_alias(player_alias)

        # Track player ref ID
        self.player_ref_id = player_ref_id
        self.aliases[player_ref_id] = player_alias

        return player_ref_id

    def add_objective_with_targets(
        self, index: int, name: str, target_count: int = 1, target_base_name: str = None
    ) -> Dict[str, Any]:
        """Add an objective with multiple targets (reference aliases)"""
        # Create the objective
        objective = self.quest.get_or_create_objective(index, name)

        # Add objective elements to quest if not already present
        obj_elements = self.quest.find_all("QOBJ")
        obj_exists = any(e for e in obj_elements if e.text == str(index))

        if not obj_exists:
            for elem in ESXElement.create_objective_elements(index, name):
                self.quest.append(elem)

        # Allocate form IDs for targets
        target_ids = self.form_id_manager.allocate_range(target_count)
        target_aliases = []

        # Create reference aliases for each target
        for i, target_id in enumerate(target_ids):
            alias_name = f"{target_base_name or name.replace(' ', '')}_Target{i + 1}"

            # Add alias elements
            alias_elements = ESXElement.create_alias_elements(
                alias_id=target_id,
                name=alias_name,
                flags="4242",  # Common flag for reference aliases
            )

            for elem in alias_elements:
                self.quest.append(elem)

            # Add target to objective
            objective.add_target(target_id)

            # Add QSTA (target data) element
            qsta = ESXElement("QSTA")
            struct = ESXElement(
                "struct", {"alias": str(target_id), "flags": "0x00000000"}
            )
            qsta.append(struct)
            self.quest.append(qsta)

            # Add condition for this target
            ctda = ESXElement.create_condition_element(alias_id=target_id)
            self.quest.append(ctda)

            # Create alias object
            alias = ESXAlias(index=target_id, name=alias_name, flags="4242")

            self.quest.add_alias(alias)
            self.aliases[target_id] = alias
            target_aliases.append(alias)

        return {
            "objective": objective,
            "target_ids": target_ids,
            "target_aliases": target_aliases,
        }

    def update_alias_count(self) -> None:
        """Update the ANAM element with the correct alias count"""
        total_aliases = len(self.aliases)

        # Find existing ANAM or create new one
        anam = self.quest.find("ANAM")
        if anam:
            anam.text = str(total_aliases)
        else:
            self.quest.append(ESXElement("ANAM", text=str(total_aliases)))

    def get_form_id_summary(self) -> Dict[str, Any]:
        """Get a summary of form ID usage"""
        return {
            "quest_id": hex(self.quest_form_id),
            "player_ref_id": hex(self.player_ref_id) if self.player_ref_id else None,
            "alias_count": len(self.aliases),
            "total_used_ids": self.form_id_manager.get_used_count(),
            "remaining_ids": 0xFFF - 0x800 + 1 - self.form_id_manager.get_used_count(),
        }


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


def validate_quest_structure(quest: ESXQuest) -> Tuple[bool, List[str]]:
    """Validate a quest structure"""
    errors = []

    # Check for required elements
    if not quest.editor_id:
        errors.append("Quest is missing editor ID")

    # Check objectives have names
    for obj in quest.objectives:
        if not obj.name:
            errors.append(f"Objective {obj.index} is missing a name")

    # Check aliases have names
    for alias in quest.aliases:
        if not alias.name:
            errors.append(f"Alias {alias.index} is missing a name")

    # Check for missing target aliases
    referenced_aliases = set()
    for obj in quest.objectives:
        for target in obj.targets:
            alias_id = target["alias"]
            referenced_aliases.add(alias_id)

    defined_aliases = {alias.index for alias in quest.aliases}
    missing_aliases = referenced_aliases - defined_aliases

    if missing_aliases:
        errors.append(f"References to non-existent aliases: {missing_aliases}")

    return (len(errors) == 0, errors)


def validate_esl_compatibility(plugin: ESXPlugin) -> Tuple[bool, List[str]]:
    """Verify if plugin meets ESL requirements"""
    return plugin.is_esl_compatible()


def hex_to_decimal(hex_str: str) -> int:
    """Convert hex string to decimal"""
    if isinstance(hex_str, int):
        return hex_str

    hex_str = str(hex_str).lower()
    if hex_str.startswith("0x"):
        return int(hex_str, 16)
    else:
        try:
            return int(hex_str, 16)
        except ValueError:
            return int(hex_str)


def decimal_to_hex(value: Union[int, str], with_prefix: bool = True) -> str:
    """Convert decimal value to hex string"""
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            # Might already be hex
            if value.lower().startswith("0x"):
                return value.lower() if with_prefix else value.lower()[2:]
            try:
                value = int(value, 16)
            except ValueError:
                raise ValueError(f"Cannot convert {value} to hex")

    prefix = "0x" if with_prefix else ""
    return f"{prefix}{value:x}"


def write_plugin_to_xml(
    plugin: ESXPlugin, output_file: str, pretty: bool = False
) -> None:
    """Write the plugin back to XML"""
    root = plugin.to_xml()
    tree = ET.ElementTree(root)

    # Add XML declaration
    if pretty:
        # Pretty format XML with indentation
        from xml.dom import minidom

        xmlstr = minidom.parseString(ET.tostring(root, encoding="UTF-8")).toprettyxml(
            indent="  "
        )
        with open(output_file, "w", encoding="UTF-8") as f:
            f.write(xmlstr)
    else:
        # Standard output without pretty printing
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
