#include "EventSink.h"

#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>
#include <collections.h>

#include "JournalManager.h"
#include "SearchForReferences.h"

RE::TESObjectREFR* mostRecentReferenceUnderCrosshair = nullptr;

EventSink* EventSink::GetSingleton() {
    static EventSink singleton;
    return &singleton;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(RE::InputEvent* const* eventPtr, RE::BSTEventSource<RE::InputEvent*>*) {
    SearchForReferences::UpdateNearbyMarkers();
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::MenuOpenCloseEvent* event, RE::BSTEventSource<RE::MenuOpenCloseEvent>*) {
    // TODO: put menu name(s) into toml config file
    if (event->opening) {
        if (event->menuName == "LootMenu") {
            if (mostRecentReferenceUnderCrosshair) SearchForReferences::DisallowObjectFromBeingMarked(mostRecentReferenceUnderCrosshair);
        } else if (event->menuName == RE::JournalMenu::MENU_NAME) {
            // FOR DEBUGGING (because we're COC-ing and need to add COC detection still)
            JournalManager::UpdateAllObjectiveNamesFromConfiguration();
        } else if (event->menuName == RE::MapMenu::MENU_NAME) {
            // if (auto* player = RE::PlayerCharacter::GetSingleton()) {
            //     for (auto markerPtr : player->currentMapMarkers) {
            //         if (auto marker = markerPtr.get()) {
            //             if (auto* extraMarker = marker->extraList.GetByType<RE::ExtraMapMarker>()) {
            //                 if (auto* mapMarkerData = extraMarker->mapData) {
            //                     mapMarkerData->locationName.fullName = "I CHANGED THE NAME";
            //                     Log("Map marker name changed to: {}", mapMarkerData->locationName.fullName.c_str());
            //                     marker->SetDisplayName("Marker Display Name!", true);
            //                 }
            //             }
            //         }
            //     }
            // }
        }
    }
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const SKSE::CrosshairRefEvent* event, RE::BSTEventSource<SKSE::CrosshairRefEvent>*) {
    if (event->crosshairRef) {
        if (auto* ref = event->crosshairRef->As<RE::TESObjectREFR>()) {
            mostRecentReferenceUnderCrosshair = ref;
            Debug("CrosshairRef is a TESObjectREFR: {:x} {}", ref->GetFormID(), ref->GetFormEditorID());
            return RE::BSEventNotifyControl::kContinue;
        } else {
            Error("CrosshairRef is not a TESObjectREFR");
        }
    }
    mostRecentReferenceUnderCrosshair = nullptr;
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESDeathEvent* event, RE::BSTEventSource<RE::TESDeathEvent>* eventSource) { return RE::BSEventNotifyControl::kContinue; }

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESActivateEvent* event, RE::BSTEventSource<RE::TESActivateEvent>* eventSource) {
    if (event->actionRef && event->actionRef->IsPlayerRef() && event->objectActivated) SearchForReferences::DisallowObjectFromBeingMarked(event->objectActivated.get());
    return RE::BSEventNotifyControl::kContinue;
}

RE::BSEventNotifyControl EventSink::ProcessEvent(const RE::TESCombatEvent* event, RE::BSTEventSource<RE::TESCombatEvent>* eventSource) {
    return RE::BSEventNotifyControl::kContinue;
}

void EventSink::Install() {
    if (auto* eventSource = RE::ScriptEventSourceHolder::GetSingleton()) {
        eventSource->AddEventSink<RE::TESDeathEvent>(EventSink::GetSingleton());
        eventSource->AddEventSink<RE::TESActivateEvent>(EventSink::GetSingleton());
        eventSource->AddEventSink<RE::TESCombatEvent>(EventSink::GetSingleton());
    } else {
        Log("Failed to get event source holder");
    }

    if (auto* deviceManager = RE::BSInputDeviceManager::GetSingleton()) deviceManager->AddEventSink(EventSink::GetSingleton());
    else Log("Failed to get input device manager");

    if (auto* ui = RE::UI::GetSingleton()) ui->AddEventSink<RE::MenuOpenCloseEvent>(EventSink::GetSingleton());
    else Log("Failed to get UI singleton");

    SKSE::GetCrosshairRefEventSource()->AddEventSink(EventSink::GetSingleton());
}
