#pragma once

#include <RE/Skyrim.h>
#include <SkyrimScripting/Logging.h>
#include <collections.h>

#include <optional>
#include <string>
#include <vector>

#include "StringUtils.h"

namespace Configuration {
    namespace Types {
        struct SKSE_Mod_Events_Names {
            std::string start_tracking_object;
            std::string stop_tracking_object;
        };

        // struct UnresolvedForm {
        //     std::string pluginName;
        //     RE::FormID  localFormId;

        //     inline static std::optional<RE::FormID> ResolveFormID(std::string_view plugin_name, RE::FormID localFormId) {
        //         Log("Resolving '{}' with local FormID {:x}", plugin_name, localFormId);
        //         const auto* plugin = RE::TESDataHandler::GetSingleton()->LookupModByName(plugin_name);
        //         if (!plugin) {
        //             Log("Plugin '{}' not found", plugin_name);
        //             return std::nullopt;  // Invalid plugin
        //         }

        //         // Special case for Skyrim.esm which should have 0 as its index (instead of 80)
        //         if (ToLowerCase(plugin->GetFilename()) == "skyrim.esm") {
        //             return localFormId;  // For Skyrim.esm, we keep the local FormID as is
        //         }

        //         if (plugin->IsLight()) {
        //             // Correctly resolve FormID for light plugins
        //             auto resolvedFormID = (localFormId & 0xFFF) | (0xFE000000 | (plugin->GetSmallFileCompileIndex() << 12));
        //             Log("Resolved FormID for light plugin '{}': {:x}", plugin_name, resolvedFormID);
        //             return resolvedFormID;
        //         } else {
        //             // Resolve FormID for regular plugins
        //             auto resolvedFormID = (localFormId & 0xFFFFFF) | (plugin->GetCompileIndex() << 24);
        //             Log("Resolved FormID for regular plugin '{}': {:x}", plugin_name, resolvedFormID);
        //             return resolvedFormID;
        //         }
        //     }

        //     inline std::optional<RE::FormID> ResolveFormID() const { return ResolveFormID(pluginName, localFormId); }

        //     template <typename T>
        //     inline T* ResolveForm() const {
        //         Log("ResolveForm() called for '{}' with local FormID {:x}", pluginName, localFormId);
        //         if (auto formId = ResolveFormID()) {
        //             Log("Resolving form ID {:x}", *formId);
        //             auto* f = RE::TESForm::LookupByID(*formId);
        //             // return RE::TESForm::LookupByID<T>(*formId);
        //             return RE::TESForm::LookupByID<T>(*formId);
        //         }
        //         return nullptr;  // Invalid form ID
        //     }
        // };

        struct JournalEntryObjective {
            std::string                   name;
            collections_set<std::string>  form_type_names;
            collections_set<RE::FormType> form_types;
            collections_set<std::string>  base_form_type_names;
            collections_set<RE::FormType> base_form_types;
            bool                          non_empty_inventory{false};
            bool                          is_dead{false};
        };

        struct JournalEntry {
            std::string                        id;
            std::string                        displayName;
            std::string                        quest;
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
