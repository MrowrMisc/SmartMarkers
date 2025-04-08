#include "EventSink.h"

#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>
#include <collections.h>

#include <mutex>
#include <optional>

#include "Constants.h"

std::string MakePascalCase(std::string_view text) {
    std::string result;
    result.reserve(text.size());
    bool capitalizeNext = true;
    for (auto c : text) {
        if (c == ' ') {
            capitalizeNext = true;
            continue;
        }
        if (capitalizeNext) {
            result += std::toupper(c);
            capitalizeNext = false;
        } else {
            result += std::tolower(c);
        }
    }
    return result;
}

std::vector<SKSE::ModCallbackEvent>        sentModEvents;
collections_map<RE::Actor*, std::uint32_t> trackedActorsToObjectiveIndexes;
std::deque<std::uint32_t>                  availableQuestAliasIndexes{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19};

std::optional<std::uint32_t> GetAvailableQuestAliasIndex() {
    static std::mutex           queueMutex;
    std::lock_guard<std::mutex> lock(queueMutex);

    if (availableQuestAliasIndexes.empty()) return std::nullopt;
    auto index = availableQuestAliasIndexes.front();
    availableQuestAliasIndexes.pop_front();
    return index;
}

void ReturnAvailableQuestAliasIndex(std::uint32_t index) { availableQuestAliasIndexes.push_back(index); }

void SetObjectiveDisplayText(RE::TESQuest* quest, std::uint32_t objectiveIndex, std::string_view text) {
    auto i = 0;
    for (auto& objective : quest->objectives) {
        if (i == objectiveIndex) {
            objective->displayText = MakePascalCase(text);
            Log("[{}] Setting objective {} text to {}", text, i, text);
            break;
        }
        ++i;
    }
}

EventSink* EventSink::GetSingleton() {
    static EventSink singleton;
    return &singleton;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESDeathEvent* event, RE::BSTEventSource<RE::TESDeathEvent>* eventSource) {
    if (event && event->dead) {
        if (auto actorDying = event->actorDying) {
            if (auto* actor = actorDying->As<RE::Actor>()) {
                if (auto* actorBase = actorDying->GetBaseObject()) {
                    if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID)) {
                        if (auto* player = RE::PlayerCharacter::GetSingleton()) {
                            auto actorName = std::string{actorBase->GetName()};
                            if (actorName.empty()) actorName = "Unknown";

                            Log("[{}] Actor died.", actorName);

                            if (actor->GetInventoryCount() == 0) {
                                Log("[{}] Actor has no inventory. Not tracking.", actorName);
                                return RE::BSEventNotifyControl::kContinue;
                            }

                            // Get the distance between the player and the actor dying
                            auto distance = actorDying->GetPosition().GetDistance(player->GetPosition());
                            Log("[{}] Distance to player: {}", actorBase->GetName(), distance);
                            if (distance >= MAX_DISTANCE_ON_DEATH) {
                                Log("[{}] Distance is greater than max distance. Not tracking.", actorName);
                                return RE::BSEventNotifyControl::kContinue;
                            }

                            if (trackedActorsToObjectiveIndexes.size() >= MAX_BODIES_TRACKED) {
                                Log("[{}] Already tracking max number of actors. Not tracking.", actorName);
                                return RE::BSEventNotifyControl::kContinue;
                            }

                            auto objectiveIndexValue = GetAvailableQuestAliasIndex();
                            if (!objectiveIndexValue) {
                                Log("[{}] No available quest alias indexes. Not tracking.", actorName);
                                return RE::BSEventNotifyControl::kContinue;
                            }

                            auto objectiveIndex  = *objectiveIndexValue;
                            auto objectiveNumber = objectiveIndex + 1;

                            trackedActorsToObjectiveIndexes.emplace(actor, objectiveIndex);
                            SetObjectiveDisplayText(quest, objectiveIndex, actorName);

                            Log("[{}] Sending mod event", actor->GetName());
                            auto& modEvent = sentModEvents.emplace_back(
                                SKSE::ModCallbackEvent{SKSE_Callback_Event_Names::TRACK_ACTOR, std::format("Body{}", objectiveNumber), static_cast<float>(objectiveNumber), actor}
                            );
                            SKSE::GetModCallbackEventSource()->SendEvent(&modEvent);
                        }
                    }
                }
            }
        }
    }
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESActivateEvent* event, RE::BSTEventSource<RE::TESActivateEvent>* eventSource) {
    if (event->actionRef && event->actionRef->IsPlayerRef() && event->objectActivated) {
        if (auto* activatedActor = event->objectActivated->As<RE::Actor>()) {
            auto found = trackedActorsToObjectiveIndexes.find(activatedActor);
            if (found != trackedActorsToObjectiveIndexes.end()) {
                auto objectiveIndex = found->second;
                auto bodyIndex      = objectiveIndex + 1;
                Log("[{}] Actor activated. Sending mod event", activatedActor->GetName());
                auto& modEvent = sentModEvents.emplace_back(
                    SKSE::ModCallbackEvent{SKSE_Callback_Event_Names::STOP_TRACKING_ACTOR, std::format("Body{}", bodyIndex), static_cast<float>(bodyIndex), activatedActor}
                );
                SKSE::GetModCallbackEventSource()->SendEvent(&modEvent);
                trackedActorsToObjectiveIndexes.erase(found);
                ReturnAvailableQuestAliasIndex(objectiveIndex);
                SetObjectiveDisplayText(RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID), objectiveIndex, "");
                Log("[{}] Actor {} removed from tracking", activatedActor->GetName(), bodyIndex);
            } else {
                Log("[{}] Actor not tracked. Not sending mod event", activatedActor->GetName());
            }
        }
    }
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESCombatEvent* event, RE::BSTEventSource<RE::TESCombatEvent>* eventSource) {
    return RE::BSEventNotifyControl::kContinue;
}

void EventSink::Install() {
    auto* eventSource = RE::ScriptEventSourceHolder::GetSingleton();
    if (eventSource) {
        eventSource->AddEventSink<RE::TESDeathEvent>(EventSink::GetSingleton());
        eventSource->AddEventSink<RE::TESActivateEvent>(EventSink::GetSingleton());
        eventSource->AddEventSink<RE::TESCombatEvent>(EventSink::GetSingleton());
    } else {
        Log("Failed to get event source holder");
    }
}
