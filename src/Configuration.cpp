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
            if (auto search_radius = tomlData["search_radius"].value<float>()) {
                newConfig->general.search_radius = *search_radius;
                Debug("[Configuration] Loaded search_radius: {}", *search_radius);
            }

            // Load journal entries
            if (auto journalEntries = tomlData["Journal"].as_table()) {
                for (const auto& [key, value] : *journalEntries) {
                    if (auto entry = value.as_table()) {
                        Types::JournalEntry journalEntry;
                        journalEntry.id = key;

                        if (auto name = entry->get("name")->value<std::string>()) {
                            journalEntry.displayName = *name;
                            Debug("[Configuration] Loaded Journal[{}].name: {}", key.data(), name->c_str());
                        }

                        if (auto quest = entry->get("quest")->as_array()) {
                            if (quest->size() == 2) {
                                journalEntry.quest.pluginName  = quest->get(0)->value<std::string>().value_or("");
                                journalEntry.quest.localFormId = quest->get(1)->value<RE::FormID>().value_or(0);
                                Debug(
                                    "[Configuration] Loaded Journal[{}].quest: pluginName={}, formId={}", key.data(), journalEntry.quest.pluginName.c_str(),
                                    journalEntry.quest.localFormId
                                );
                            }
                        }

                        journalEntry.objective_count = entry->get("objective_count")->value<std::uint32_t>().value_or(0);
                        Debug("[Configuration] Loaded Journal[{}].objective_count: {}", key.data(), journalEntry.objective_count);

                        journalEntry.reference_aliases_per_objective = entry->get("reference_aliases_per_objective")->value<std::uint32_t>().value_or(0);
                        Debug("[Configuration] Loaded Journal[{}].reference_aliases_per_objective: {}", key.data(), journalEntry.reference_aliases_per_objective);

                        if (auto objectivesNode = entry->get("objective")) {
                            if (auto objectives = objectivesNode->as_array()) {
                                for (const auto& obj : *objectives) {
                                    if (auto objTable = obj.as_table()) {
                                        Types::JournalEntryObjective objective;
                                        objective.name = objTable->get("name")->value<std::string>().value_or("");
                                        Debug("[Configuration] Loaded Journal[{}].objective.name: {}", key.data(), objective.name.c_str());

                                        if (auto formTypeNode = objTable->get("form_type")) {
                                            if (auto formType = formTypeNode->value<std::string>()) {
                                                objective.form_type_names.insert(*formType);
                                                auto formTypeValue = RE::StringToFormType(*formType);
                                                if (formTypeValue != RE::FormType::None) {
                                                    objective.form_types.insert(formTypeValue);
                                                }
                                                Debug("[Configuration] Loaded Journal[{}].objective.form_type: {}", key.data(), formType->c_str());
                                            }
                                        }

                                        if (auto baseFormTypeNode = objTable->get("base_form_type")) {
                                            if (auto baseFormType = baseFormTypeNode->value<std::string>()) {
                                                objective.base_form_type_names.insert(*baseFormType);
                                                auto baseFormTypeValue = RE::StringToFormType(*baseFormType);
                                                if (baseFormTypeValue != RE::FormType::None) {
                                                    objective.base_form_types.insert(baseFormTypeValue);
                                                }
                                                Debug("[Configuration] Loaded Journal[{}].objective.base_form_type: {}", key.data(), baseFormType->c_str());
                                            }
                                        }

                                        if (auto nonEmptyInventory = objTable->get("non_empty_inventory")) {
                                            objective.non_empty_inventory = nonEmptyInventory->value<bool>().value_or(false);
                                            Debug("[Configuration] Loaded Journal[{}].objective.non_empty_inventory: {}", key.data(), objective.non_empty_inventory);
                                        }

                                        if (auto isDead = objTable->get("is_dead")) {
                                            objective.is_dead = isDead->value<bool>().value_or(false);
                                            Debug("[Configuration] Loaded Journal[{}].objective.is_dead: {}", key.data(), objective.is_dead);
                                        }

                                        journalEntry.objectives.push_back(objective);
                                    }
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
                Debug("[Configuration] Loaded SKSE_Mod_Events_Names.start_tracking_object: {}", newConfig->skse_mod_events_names.start_tracking_object.c_str());

                newConfig->skse_mod_events_names.stop_tracking_object = skseEvents->get("stop_tracking_object")->value<std::string>().value_or("");
                Debug("[Configuration] Loaded SKSE_Mod_Events_Names.stop_tracking_object: {}", newConfig->skse_mod_events_names.stop_tracking_object.c_str());
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
