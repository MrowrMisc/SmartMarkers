#include "ReferenceMatcher.h"

inline bool DoesReferenceHaveNonEmptyInventory(RE::TESObjectREFR* ref) {
    if (auto* baseObject = ref->GetBaseObject()) {
        if (baseObject->GetFormType() == RE::FormType::Container || ref->IsDead()) {
            for (auto& [object, data] : ref->GetInventory()) {
                if (data.first > 0 && object) {
                    std::string_view name = object->GetName();
                    if (name.empty()) continue;
                    return true;
                }
            }
        }
    }
    return false;
}

bool ReferenceMatchesObjective(RE::TESObjectREFR* ref, Configuration::Types::JournalEntryObjective* objective) {
    if (!objective) return false;
    if (!ref) return false;
    if (ref->IsDeleted()) return false;
    if (!objective->form_types.empty() && !objective->form_types.contains(ref->GetFormType())) return false;
    if (objective->non_empty_inventory && !DoesReferenceHaveNonEmptyInventory(ref)) return false;
    if (objective->is_dead && !ref->IsDead()) return false;
    if (!objective->base_form_types.empty()) {
        if (auto* baseForm = ref->GetBaseObject()) {
            if (!objective->base_form_types.contains(baseForm->GetFormType())) return false;
        }
    }
    return true;
}