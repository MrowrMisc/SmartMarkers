#include "EventSink.h"

#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>

#include "Constants.h"

std::uint32_t                       nextQuestAliasIndex = 0;
std::vector<SKSE::ModCallbackEvent> sentModEvents;

EventSink* EventSink::GetSingleton() {
    static EventSink singleton;
    return &singleton;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESDeathEvent* event, RE::BSTEventSource<RE::TESDeathEvent>* eventSource) override {
    if (event && event->dead) {
        if (auto actorDying = event->actorDying) {
            if (auto* actor = actorDying->As<RE::Actor>()) {
                if (auto* actorBase = actorDying->GetBaseObject()) {
                    if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID)) {
                        if (auto* player = RE::PlayerCharacter::GetSingleton()) {
                            // Get the distance between the player and the actor dying
                            auto distance = actorDying->GetPosition().GetDistance(player->GetPosition());
                            Log("{} died. Distance to player: {}", actorBase->GetName(), distance);
                            auto questAliasIndex = nextQuestAliasIndex++;
                            Log("Sending mod event for actor: {}", actor->GetName());
                            auto& modEvent = sentModEvents.emplace_back(SKSE::ModCallbackEvent{"MP_WhereAreTheBodies_TrackActor", "", static_cast<float>(questAliasIndex), actor});
                            SKSE::GetModCallbackEventSource()->SendEvent(&modEvent);
                            Log("Sent mod event for actor: {}", actor->GetName());
                        }
                    }
                }
            }
        }
    }
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESActivateEvent* event, RE::BSTEventSource<RE::TESActivateEvent>* eventSource) override {
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESCombatEvent* event, RE::BSTEventSource<RE::TESCombatEvent>* eventSource) override {
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
