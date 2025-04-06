#include "EventSink.h"

#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>
#include <collections.h>

#include "Constants.h"

std::uint32_t                              nextQuestAliasIndex = 0;
std::vector<SKSE::ModCallbackEvent>        sentModEvents;
collections_map<RE::Actor*, std::uint32_t> trackedActorsToObjectiveIndexes;

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

                            auto objectiveIndex = nextQuestAliasIndex++;
                            auto bodyIndex      = objectiveIndex + 1;

                            trackedActorsToObjectiveIndexes.emplace(actor, objectiveIndex);

                            auto i = 0;
                            for (auto& objective : quest->objectives) {
                                if (i == objectiveIndex) {
                                    objective->displayText = actorName;
                                    Log("[{}] Setting objective {} text to {}", actorName, i, actorName);
                                    break;
                                }
                                ++i;
                            }

                            Log("[{}] Sending mod event", actor->GetName());
                            auto& modEvent = sentModEvents.emplace_back(
                                SKSE::ModCallbackEvent{SKSE_Callback_Event_Names::TRACK_ACTOR, std::format("Body{}", bodyIndex), static_cast<float>(bodyIndex), actor}
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
