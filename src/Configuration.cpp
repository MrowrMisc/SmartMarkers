#include "Configuration.h"

#include <RE/Skyrim.h>
#include <SkyrimScripting/Logging.h>
#include <toml++/toml.h>

#include <filesystem>
#include <memory>

namespace Configuration {

    namespace {
        std::filesystem::path                 TOML_CONFIG_FILE_PATH = "Data/SKSE/Plugins/SmartMarkers.toml";
        std::unique_ptr<Types::Configuration> _config;
    }

    void ReloadConfig() {
        try {
            auto tomlData = toml::parse_file(TOML_CONFIG_FILE_PATH.string());

            auto newConfig = std::make_unique<Types::Configuration>();

            // Load general settings
            if (auto general = tomlData["general"].as_table()) {
                if (auto search_radius = general->get("search_radius")->value<float>()) newConfig->general.search_radius = *search_radius;
            }

            // Load journal entries
            if (auto journalEntries = tomlData["Journal"].as_table()) {
                for (const auto& [key, value] : *journalEntries) {
                    if (auto entry = value.as_table()) {
                        Types::JournalEntry journalEntry;
                        journalEntry.id = key;

                        if (auto name = entry->get("name")->value<std::string>()) journalEntry.displayName = *name;

                        if (auto quest = entry->get("quest")->as_array()) {
                            if (quest->size() == 2) {
                                journalEntry.quest.pluginName = quest->get(0)->value<std::string>().value_or("");
                                journalEntry.quest.formId     = quest->get(1)->value<RE::FormID>().value_or(0);
                            }
                        }

                        journalEntry.objective_count                 = entry->get("objective_count")->value<std::uint32_t>().value_or(0);
                        journalEntry.reference_aliases_per_objective = entry->get("reference_aliases_per_objective")->value<std::uint32_t>().value_or(0);

                        if (auto objectives = entry->get("objective")->as_array()) {
                            for (const auto& obj : *objectives) {
                                if (auto objTable = obj.as_table()) {
                                    Types::JournalEntryObjective objective;
                                    objective.name = objTable->get("name")->value<std::string>().value_or("");
                                    if (auto formType = objTable->get("form_type")->value<std::string>()) {
                                        objective.form_type_names.insert(*formType);
                                        auto formTypeValue = RE::StringToFormType(*formType);
                                        if (formTypeValue != RE::FormType::None) objective.form_types.insert(formTypeValue);
                                    }
                                    objective.non_empty_inventory = objTable->get("non_empty_inventory")->value<bool>().value_or(false);
                                    journalEntry.objectives.push_back(objective);
                                }
                            }
                        }

                        newConfig->journal_entries.try_emplace(std::string(key), std::move(journalEntry));
                    }
                }
            }

            // Load SKSE mod events
            if (auto skseEvents = tomlData["SKSE_Mod_Events_Names"].as_table()) {
                newConfig->skse_mod_events_names.start_tracking_object = skseEvents->get("start_tracking_object")->value<std::string>().value_or("");
                newConfig->skse_mod_events_names.stop_tracking_object  = skseEvents->get("stop_tracking_object")->value<std::string>().value_or("");
            }

            _config = std::move(newConfig);
        } catch (const toml::parse_error& e) {
            Error("[Configuration] Failed to parse TOML file: {}", e.description());
        } catch (const std::exception& e) {
            Error("[Configuration] Exception during config reload: {}", e.what());
        }
    }

    Types::Configuration* GetConfig() {
        if (!_config) ReloadConfig();
        if (!_config) {
            Error("[Configuration] Failed to load configuration");
            return nullptr;
        }
        return _config.get();
    }
}
