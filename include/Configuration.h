#pragma once

#include <RE/Skyrim.h>
#include <collections.h>

#include <string>
#include <vector>

namespace Configuration {
    namespace Types {
        struct SKSE_Mod_Events_Names {
            std::string start_tracking_object;
            std::string stop_tracking_object;
        };

        struct UnresolvedForm {
            std::string pluginName;
            RE::FormID  formId;
        };

        struct JournalEntryObjective {
            std::string                   name;
            collections_set<std::string>  form_type_names;
            collections_set<RE::FormType> form_types;
            bool                          non_empty_inventory{false};

            inline bool MatchesFormType(const RE::FormType& formType) const { return form_types.empty() || form_types.contains(formType); }
        };

        struct JournalEntry {
            std::string                        id;
            std::string                        displayName;
            UnresolvedForm                     quest;
            std::uint32_t                      objective_count;
            std::uint32_t                      reference_aliases_per_objective;
            std::vector<JournalEntryObjective> objectives;
        };

        struct General {
            float search_radius;
        };

        struct Configuration {
            General                                    general;
            collections_map<std::string, JournalEntry> journal_entries;
            SKSE_Mod_Events_Names                      skse_mod_events_names;
        };
    }

    // Reloads configuration from the TOML file
    void ReloadConfig();

    Types::Configuration* GetConfig();
}
