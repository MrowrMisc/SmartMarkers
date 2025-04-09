#pragma once

#include <RE/Skyrim.h>

class EventSink : public RE::BSTEventSink<RE::InputEvent*>,
                  public RE::BSTEventSink<RE::TESDeathEvent>,
                  public RE::BSTEventSink<RE::TESActivateEvent>,
                  public RE::BSTEventSink<RE::TESCombatEvent> {
public:
    static EventSink* GetSingleton();
    static void       Install();

    RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* eventPtr, RE::BSTEventSource<RE::InputEvent*>*) override;
    RE::BSEventNotifyControl ProcessEvent(const RE::TESDeathEvent* event, RE::BSTEventSource<RE::TESDeathEvent>* eventSource) override;
    RE::BSEventNotifyControl ProcessEvent(const RE::TESActivateEvent* event, RE::BSTEventSource<RE::TESActivateEvent>* eventSource) override;
    RE::BSEventNotifyControl ProcessEvent(const RE::TESCombatEvent* event, RE::BSTEventSource<RE::TESCombatEvent>* eventSource) override;
};
