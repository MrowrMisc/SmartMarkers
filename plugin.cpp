#include <SkyrimScripting/Plugin.h>
#include <collections.h>

#include <deque>

#include "SetQuestObjectiveState.h"

constexpr auto QUEST_EDITOR_ID = "MP_WhereAreTheBodies_Quest";

std::uint32_t          _nextQuestAliasIndex = 0;
std::deque<RE::Actor*> recentlyKilledNeabyActors;
// std::deque<std::uint32_t> availableQuestAliasIndexes;

std::vector<RE::NiPointer<RE::TESObjectREFR>> actorSmartPointers;
std::vector<SKSE::ModCallbackEvent>           sentModEvents;

void OnGameLoad() {
    if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID)) {
        Log("Found quest with editor ID: {}", QUEST_EDITOR_ID);
        if (auto* objective = quest->objectives.front()) {
            if (!objective->state.any(RE::QUEST_OBJECTIVE_STATE::kDisplayed)) {
                Log("Found quest with editor ID: {}, activating...", QUEST_EDITOR_ID);
                objective->flags.reset(RE::QUEST_OBJECTIVE_FLAGS::kNoStatsTracking);
                SetObjectiveState(quest->objectives.front(), RE::QUEST_OBJECTIVE_STATE::kDisplayed);
            }
        }
    } else {
        Log("Failed to find quest with editor ID: {}", QUEST_EDITOR_ID);
    }
}

class EventSink : public RE::BSTEventSink<RE::TESDeathEvent>, public RE::BSTEventSink<RE::TESActivateEvent>, public RE::BSTEventSink<RE::TESCombatEvent> {
    void TrackDeadActor(RE::Actor* actor) {
        if (recentlyKilledNeabyActors.size() > 35) {
            Log("Too many dead actors :(");
            return;
        }

        Log("Tracking dead actor: {}", actor->GetName());
        if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID)) {
            if (actor && actor->IsDead()) {
                Log("Tracking dead actor: {}", actor->GetName());

                // Track here in memory
                recentlyKilledNeabyActors.push_back(actor);
                if (recentlyKilledNeabyActors.size() > 35) {
                    Log("Too many dead actors :(");
                    return;
                }

                auto questAliasIndex = _nextQuestAliasIndex++;

                // Now track in the next quest alias..
                // quest->objectives.front()->targets[0]->alias
                if (auto* referenceAlias = skyrim_cast<RE::BGSRefAlias*>(quest->aliases[questAliasIndex])) {
                    Log("Tracking dead actor in quest alias: {} in alias index {}", actor->GetName(), questAliasIndex);

                    RE::NiPointer<RE::TESObjectREFR> refSmart;
                    refSmart.reset(actor);
                    actorSmartPointers.push_back(refSmart);
                    RE::ObjectRefHandle handle = RE::BSPointerHandleManagerInterface<RE::TESObjectREFR>::GetHandle(refSmart.get());

                    // RE::ObjectRefHandle handle;
                    // handle = RE::BSPointerHandleManagerInterface<RE::TESObjectREFR>::GetHandle(actor);

                    referenceAlias->fillType                  = RE::BGSRefAlias::FILL_TYPE::kForced;
                    referenceAlias->fillData.forced.forcedRef = handle;

                    quest->CreateRefHandleByAliasID(referenceAlias->fillData.forced.forcedRef, questAliasIndex);

                    auto theHandle = referenceAlias->fillData.forced.forcedRef;
                    auto resolved  = theHandle.get();
                    if (!resolved) {
                        Log("Alias handle could not resolve to a ref!");
                    } else {
                        Log("Alias handle resolved to: {}", resolved->GetName());
                    }

                    // quest->objectives.front()->targets[0].
                }

                // if (recentlyKilledNeabyActors.size() > 35) {
                //     //
                //     recentlyKilledNeabyActors.pop_front();
                // }
            }
        }
    }

public:
    static EventSink* GetSingleton() {
        static EventSink singleton;
        return &singleton;
    }

    RE::BSEventNotifyControl ProcessEvent(const RE::TESDeathEvent* event, RE::BSTEventSource<RE::TESDeathEvent>* eventSource) override {
        if (event && event->dead) {
            if (auto actorDying = event->actorDying) {
                if (auto* actor = actorDying->As<RE::Actor>()) {
                    if (auto* actorBase = actorDying->GetBaseObject()) {
                        if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID)) {
                            if (auto* player = RE::PlayerCharacter::GetSingleton()) {
                                // Get the distance between the player and the actor dying
                                auto distance = actorDying->GetPosition().GetDistance(player->GetPosition());
                                Log("{} died. Distance to player: {}", actorBase->GetName(), distance);

                                // Cuz of coc stuff
                                OnGameLoad();

                                // SKSE::GetTaskInterface()->AddUITask([&]() { TrackDeadActor(actor); });

                                // RE::NiPointer<RE::Actor> safeActor(actor);  // Strong smart pointer

                                // SKSE::GetTaskInterface()->AddUITask([safeActor]() {
                                //     if (safeActor && safeActor->IsDead()) {
                                //         EventSink::GetSingleton()->TrackDeadActor(safeActor.get());
                                //     }
                                // });

                                // RE::BSTSmartPointer<RE::BGSMod::Attachment::ModCallbackEvent> modEvent = new RE::BGSMod::Attachment::ModCallbackEvent();

                                auto questAliasIndex = _nextQuestAliasIndex++;

                                Log("Sending mod event for actor: {}", actor->GetName());
                                auto& modEvent =
                                    sentModEvents.emplace_back(SKSE::ModCallbackEvent{"MP_WhereAreTheBodies_TrackActor", "", static_cast<float>(questAliasIndex), actor});
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

    RE::BSEventNotifyControl ProcessEvent(const RE::TESActivateEvent* event, RE::BSTEventSource<RE::TESActivateEvent>* eventSource) override {
        return RE::BSEventNotifyControl::kContinue;
    }

    RE::BSEventNotifyControl ProcessEvent(const RE::TESCombatEvent* event, RE::BSTEventSource<RE::TESCombatEvent>* eventSource) override {
        return RE::BSEventNotifyControl::kContinue;
    }
};

SKSEPlugin_OnNewGame { OnGameLoad(); }
SKSEPlugin_OnPostLoadGame { OnGameLoad(); }

SKSEPlugin_Entrypoint {
    Log("Latest version...");

    auto* eventSource = RE::ScriptEventSourceHolder::GetSingleton();
    if (eventSource) {
        eventSource->AddEventSink<RE::TESDeathEvent>(EventSink::GetSingleton());
        eventSource->AddEventSink<RE::TESActivateEvent>(EventSink::GetSingleton());
        eventSource->AddEventSink<RE::TESCombatEvent>(EventSink::GetSingleton());
    } else {
        Log("Failed to get event source holder");
    }
}
