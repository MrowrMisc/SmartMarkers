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

        struct JournalEntryObjectives {
            std::string                   name;
            collections_set<std::string>  form_type_names;
            collections_set<RE::FormType> form_types;
            // collections_set<std::string> base_object_form_type_names;
            // collections_set<RE::FormType> base_object_form_types;
            // collections_set<std::string> name_contains_matchers;
            // Would wanna pre-compile these regexes and store them too...
            // collections_set<std::string> name_regex_matchers;
        };

        struct JournalEntry {
            std::string                         id;
            std::string                         displayName;
            UnresolvedForm                      quest;
            std::uint32_t                       objective_count;
            std::uint32_t                       reference_aliases_per_objective;
            std::vector<JournalEntryObjectives> objectives;
        };
    }
}
