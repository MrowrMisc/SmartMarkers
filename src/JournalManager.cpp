#include "JournalManager.h"

#include <SkyrimScripting/Logging.h>

#include "Configuration.h"

namespace JournalManager {
    void SetObjectiveName(RE::TESQuest* quest, std::uint32_t questObjectiveIndex, std::string_view name) {}

    inline RE::BGSQuestObjective* GetObjective(RE::TESQuest* quest, std::uint32_t index) {
        if (quest) {
            auto i = 0;
            for (auto& objective : quest->objectives) {
                if (i == index) return objective;
                ++i;
            }
            Log("Failed to get objective {} from quest {}", index, quest->GetFormEditorID());
        } else {
            Log("Invalid quest passed to GetObjective");
        }
        return nullptr;
    }

    void UpdateAllObjectiveNamesFromConfiguration() {
        Log("Updating all objective names from configuration");
        for (auto& [id, journalEntry] : Configuration::GetConfig()->journal_entries) {
            if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(journalEntry.quest)) {
                quest->fullName = journalEntry.displayName;

                // Try this...
                // quest->data.questType.set(RE::QUEST_DATA::Type::kSideQuest)

                Log("Set {} quest name to {}", quest->GetFormEditorID(), journalEntry.displayName.c_str());
                auto objectiveIndex = 0;
                for (auto& objective : journalEntry.objectives) {
                    if (auto* questObjective = GetObjective(quest, objectiveIndex)) {
                        questObjective->displayText = objective.name;
                        Log("Set {} objective {} name to {}", quest->GetFormEditorID(), objectiveIndex, objective.name.c_str());
                    }
                    objectiveIndex++;
                }
            }
        }
    }
}