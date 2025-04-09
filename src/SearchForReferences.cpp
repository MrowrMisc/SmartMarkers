#include "SearchForReferences.h"

#include <RE/Skyrim.h>
#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>
#include <collections.h>

#include <atomic>
#include <chrono>

#include "Constants.h"

// TODO: the logs here should be ::trace ones, most of them, cause there will be a lot of them

namespace SearchForReferences {

    namespace {
        std::vector<SKSE::ModCallbackEvent> sentModEvents;  // For now, keep forever LOL

        constexpr std::chrono::seconds                     updateInterval(2);  // Moved before lastRunTime
        std::atomic<bool>                                  isRunning(false);
        std::atomic<std::chrono::steady_clock::time_point> lastRunTime(std::chrono::steady_clock::now() - updateInterval);
        constexpr auto                                     maxDistance = 1000.0f;
        collections_set<RE::TESObjectREFR*>                currentlyMarkedNearbyObjects;

        auto                                               currentlyTrackingCount = 0;
        collections_map<RE::TESObjectREFR*, std::uint32_t> trackedObjectRefsToIndexes;

        inline void TellPapyrusToTrackReference(RE::TESObjectREFR* ref) {
            if (currentlyTrackingCount >= 10) {
                Log("[{}] Already tracking max number of actors. Not tracking.", ref->GetName());
                return;
            }
            currentlyTrackingCount++;
            // auto objectiveIndexValue = GetAvailableQuestAliasIndex();
            trackedObjectRefsToIndexes[ref] = currentlyTrackingCount;
            auto& modEvent =
                sentModEvents.emplace_back(SKSE::ModCallbackEvent{SKSE_Callback_Event_Names::TRACK_ACTOR, std::format("Objective1_{}", currentlyTrackingCount), 0.0f, ref});
            SKSE::GetModCallbackEventSource()->SendEvent(&modEvent);
        }

        inline void TellPapyrusToUntrackReference(RE::TESObjectREFR* ref) {
            auto found = trackedObjectRefsToIndexes.find(ref);
            if (found == trackedObjectRefsToIndexes.end()) {
                Log("[{}] Not tracked. Not untracking.", ref->GetName());
                return;
            }
            auto  objectiveIndex = found->second;
            auto& modEvent =
                sentModEvents.emplace_back(SKSE::ModCallbackEvent{SKSE_Callback_Event_Names::STOP_TRACKING_ACTOR, std::format("Objective1_{}", objectiveIndex), 0.0f, ref});
            SKSE::GetModCallbackEventSource()->SendEvent(&modEvent);
            currentlyTrackingCount--;
        }
    }

    void UpdateNearbyMarkers() {
        if (isRunning.exchange(true)) return;

        auto now     = std::chrono::steady_clock::now();
        auto lastRun = lastRunTime.load();
        if (now - lastRun < updateInterval) {
            isRunning.store(false);
            return;
        }

        lastRunTime.store(now);

        auto startTime = std::chrono::steady_clock::now();

        // Ensure we are in-game
        auto* ui = RE::UI::GetSingleton();
        if (!ui || ui->IsMenuOpen(RE::MainMenu::MENU_NAME) || ui->IsMenuOpen(RE::LoadingMenu::MENU_NAME) || ui->GameIsPaused()) {
            isRunning.store(false);
            return;
        }

        // Perform the update operation
        auto* tes = RE::TES::GetSingleton();
        if (!tes) {
            isRunning.store(false);
            return;
        }

        auto* player = RE::PlayerCharacter::GetSingleton();
        if (!player) {
            isRunning.store(false);
            return;
        }

        collections_set<RE::TESObjectREFR*> newlyDiscoveredNearbyObjectsToMark;

        tes->ForEachReferenceInRange(player, maxDistance, [&](RE::TESObjectREFR* ref) {
            if (ref == player) return RE::BSContainer::ForEachResult::kContinue;
            if (ref && !ref->IsDeleted()) {
                if (auto* baseObject = ref->GetBaseObject()) {
                    if (baseObject->GetFormType() == RE::FormType::Container || ref->IsDead()) {
                        if (auto* container = ref->GetContainer()) {
                            if (container->numContainerObjects > 0) {
                                newlyDiscoveredNearbyObjectsToMark.insert(ref);
                            }
                        }
                    }
                }
            }
            return RE::BSContainer::ForEachResult::kContinue;
        });

        for (auto& ref : newlyDiscoveredNearbyObjectsToMark) {
            if (currentlyMarkedNearbyObjects.find(ref) == currentlyMarkedNearbyObjects.end()) {
                Log("[{}] Marking nearby object", ref->GetName());
                currentlyMarkedNearbyObjects.insert(ref);
                TellPapyrusToTrackReference(ref);
            }
        }

        for (auto& ref : currentlyMarkedNearbyObjects) {
            if (newlyDiscoveredNearbyObjectsToMark.find(ref) == newlyDiscoveredNearbyObjectsToMark.end()) {
                Log("[{}] Unmarking nearby object", ref->GetName());
                currentlyMarkedNearbyObjects.erase(ref);
                TellPapyrusToUntrackReference(ref);
            }
        }

        auto endTime = std::chrono::steady_clock::now();

        isRunning.store(false);
    }
}