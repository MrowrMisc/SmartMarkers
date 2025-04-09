#pragma once

#include <RE/Skyrim.h>
#include <SKSE/SKSE.h>

class EventSink : public RE::BSTEventSink<RE::InputEvent*>,
                  public RE::BSTEventSink<RE::MenuOpenCloseEvent>,
                  public RE::BSTEventSink<SKSE::CrosshairRefEvent>,
                  public RE::BSTEventSink<RE::TESDeathEvent>,
                  public RE::BSTEventSink<RE::TESActivateEvent>,
                  public RE::BSTEventSink<RE::TESCombatEvent> {
public:
    static EventSink* GetSingleton();
    static void       Install();

    RE::BSEventNotifyControl ProcessEvent(RE::InputEvent* const* eventPtr, RE::BSTEventSource<RE::InputEvent*>*) override;
    RE::BSEventNotifyControl ProcessEvent(const RE::MenuOpenCloseEvent* event, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) override;
    RE::BSEventNotifyControl ProcessEvent(const SKSE::CrosshairRefEvent* event, RE::BSTEventSource<SKSE::CrosshairRefEvent>*) override;
    RE::BSEventNotifyControl ProcessEvent(const RE::TESDeathEvent* event, RE::BSTEventSource<RE::TESDeathEvent>* eventSource) override;
    RE::BSEventNotifyControl ProcessEvent(const RE::TESActivateEvent* event, RE::BSTEventSource<RE::TESActivateEvent>* eventSource) override;
    RE::BSEventNotifyControl ProcessEvent(const RE::TESCombatEvent* event, RE::BSTEventSource<RE::TESCombatEvent>* eventSource) override;
};
