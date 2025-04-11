#include "SearchForReferences.h"

#include <RE/Skyrim.h>
#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>
#include <collections.h>

#include <atomic>
#include <chrono>

#include "Configuration.h"
#include "Constants.h"
#include "ReferenceMatcher.h"

namespace SearchForReferences {

    namespace {
        std::vector<SKSE::ModCallbackEvent>                                                   sentModEvents;      // For now, keep forever LOL
        constexpr std::chrono::seconds                                                        updateInterval(2);  // Moved before lastRunTime
        std::atomic<bool>                                                                     isRunning(false);
        std::atomic<bool>                                                                     isDisabled{false};
        std::atomic<std::chrono::steady_clock::time_point>                                    lastRunTime(std::chrono::steady_clock::now() - updateInterval);
        collections_map<Configuration::Types::JournalEntryObjective*, MarkerDataForObjective> markerDataForObjectives;

        inline void TellPapyrusToTrackReference(RE::TESObjectREFR* ref, MarkerDataForObjective& markerDataForObjective) {
            if (markerDataForObjective.currentlyTrackingCount >= 50) {  // markerDataForObjective.objective....
                Log("[{}] Already tracking max number of actors. Not tracking.", ref->GetName());
                return;
            }
            Debug("> [{}] Telling Papyrus to track reference '{}' {:x}", markerDataForObjective.objective->name, ref->GetName(), ref->GetFormID());
            markerDataForObjective.currentlyTrackingCount++;
            markerDataForObjective.trackedObjectRefsToIndexes[ref] = markerDataForObjective.currentlyTrackingCount;
            auto& modEvent                                         = sentModEvents.emplace_back(
                SKSE::ModCallbackEvent{SKSE_Callback_Event_Names::TRACK_ACTOR, std::format("Objective1_{}", markerDataForObjective.currentlyTrackingCount), 0.0f, ref}
            );
            SKSE::GetModCallbackEventSource()->SendEvent(&modEvent);
        }

        inline void TellPapyrusToUntrackReference(RE::TESObjectREFR* ref, MarkerDataForObjective& markerDataForObjective) {
            auto found = markerDataForObjective.trackedObjectRefsToIndexes.find(ref);
            if (found == markerDataForObjective.trackedObjectRefsToIndexes.end()) {
                Log("[{}] Not tracked. Not untracking.", ref->GetName());
                return;
            }
            Debug("> [{}] Telling Papyrus to untrack reference '{}' {:x}", markerDataForObjective.objective->name, ref->GetName(), ref->GetFormID());
            auto  objectiveIndex = found->second;
            auto& modEvent =
                sentModEvents.emplace_back(SKSE::ModCallbackEvent{SKSE_Callback_Event_Names::STOP_TRACKING_ACTOR, std::format("Objective1_{}", objectiveIndex), 0.0f, ref});
            SKSE::GetModCallbackEventSource()->SendEvent(&modEvent);
            markerDataForObjective.currentlyTrackingCount--;
            markerDataForObjective.trackedObjectRefsToIndexes.erase(found);
        }

    }

    void ResetAllCollections() {
        Log("Resetting all collections");
        sentModEvents.clear();
        markerDataForObjectives.clear();
        isRunning.store(false);
        lastRunTime.store(std::chrono::steady_clock::now() - updateInterval);
        for (auto& [journalEntryId, journalEntry] : Configuration::GetConfig()->journal_entries) {
            for (auto& objective : journalEntry.objectives) {
                auto result = markerDataForObjectives.emplace(&objective, MarkerDataForObjective{});
                if (result.second) {
                    auto& markerDataForObjective     = result.first->second;
                    markerDataForObjective.objective = &objective;
                }
            }
        }
        Log("All collections reset");
    }

    void DisallowObjectFromBeingMarked(RE::TESObjectREFR* ref, MarkerDataForObjective& markerDataForObjective) {
        if (ref) {
            markerDataForObjective.theseObjectsHaveBeenInteractedWith.insert(ref);
            Log("~ [{}] Disallowing object from being marked", ref->GetName());
            if (markerDataForObjective.trackedObjectRefsToIndexes.find(ref) != markerDataForObjective.trackedObjectRefsToIndexes.end()) {
                TellPapyrusToUntrackReference(ref, markerDataForObjective);
            }
        }
    }

    void DisallowObjectFromBeingMarked(RE::TESObjectREFR* ref) {
        if (ref) {
            for (auto& [objective, markerData] : markerDataForObjectives) {
                Log("~ [{}] Disallowing object from being marked for {}", ref->GetName(), objective->name.c_str());
                DisallowObjectFromBeingMarked(ref, markerData);
            }
        }
    }

    inline bool IsObjectDisallowed(RE::TESObjectREFR* ref, MarkerDataForObjective& markerDataForObjective) {
        if (ref) {
            auto found = markerDataForObjective.theseObjectsHaveBeenInteractedWith.find(ref);
            if (found != markerDataForObjective.theseObjectsHaveBeenInteractedWith.end()) return true;
        }
        return false;
    }

    void UpdateNearbyMarkers() {
        if (isDisabled) return;
        if (isRunning.exchange(true)) return;

        auto maxDistance = Configuration::GetConfig()->general.search_radius;
        if (maxDistance <= 0) {
            Log("Search radius is 0. Not searching.");
            isDisabled = true;
            return;
        }

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

        collections_map<MarkerDataForObjective*, collections_set<RE::TESObjectREFR*>> newlyDiscoveredNearbyObjectsToMark;

        auto searchedReferenceCount = 0;
        tes->ForEachReferenceInRange(player, maxDistance, [&](RE::TESObjectREFR* ref) {
            searchedReferenceCount++;
            if (ref == player) return RE::BSContainer::ForEachResult::kContinue;
            for (auto& [objective, markerData] : markerDataForObjectives) {
                if (ReferenceMatchesObjective(ref, objective)) {
                    Trace("Found reference '{}' {:x} matching objective '{}'", ref->GetName(), ref->GetFormID(), objective->name.c_str());
                    newlyDiscoveredNearbyObjectsToMark[&markerData].insert(ref);
                    // TellPapyrusToTrackReference(ref, markerData);
                }
            }
            return RE::BSContainer::ForEachResult::kContinue;
        });
        Debug("Searched {} references in range", searchedReferenceCount);

        // for (auto& [objective, markerData] : markerDataForObjectives) {
        //     auto found = newlyDiscoveredNearbyObjectsToMark.find(&markerData);
        //     if (found == newlyDiscoveredNearbyObjectsToMark.end()) continue;
        //     for (auto& ref : found->second) {
        //         if (IsObjectDisallowed(ref, markerData)) continue;
        //         if (markerData.currentlyMarkedNearbyObjects.find(ref) == markerData.currentlyMarkedNearbyObjects.end()) {
        //             markerData.currentlyMarkedNearbyObjects.insert(ref);
        //             Log(">> [{}] Tracking reference '{}'", markerData.objective->name.c_str(), ref->GetName());
        //             TellPapyrusToTrackReference(ref, markerData);
        //         }
        //     }
        // }

        // for (auto& [objective, markerData] : markerDataForObjectives) {
        //     auto found = newlyDiscoveredNearbyObjectsToMark.find(&markerData);
        //     if (found == newlyDiscoveredNearbyObjectsToMark.end()) continue;
        //     for (auto& ref : found->second) {
        //         if (IsObjectDisallowed(ref, markerData)) continue;
        //         if (markerData.currentlyMarkedNearbyObjects.find(ref) != markerData.currentlyMarkedNearbyObjects.end()) {
        //             markerData.currentlyMarkedNearbyObjects.erase(ref);
        //             Log(">> [{}] Untracking reference '{}'", markerData.objective->name.c_str(), ref->GetName());
        //             TellPapyrusToUntrackReference(ref, markerData);
        //         }
        //     }
        // }

        // ...existing code...

        for (auto& [objective, markerData] : markerDataForObjectives) {
            auto found = newlyDiscoveredNearbyObjectsToMark.find(&markerData);
            if (found == newlyDiscoveredNearbyObjectsToMark.end()) continue;

            // Track new references
            for (auto& ref : found->second) {
                if (IsObjectDisallowed(ref, markerData)) continue;
                if (markerData.currentlyMarkedNearbyObjects.find(ref) == markerData.currentlyMarkedNearbyObjects.end()) {
                    markerData.currentlyMarkedNearbyObjects.insert(ref);
                    Log(">> [{}] Tracking reference '{}'", markerData.objective->name.c_str(), ref->GetName());
                    TellPapyrusToTrackReference(ref, markerData);
                }
            }

            // Untrack references that are no longer valid
            for (auto it = markerData.currentlyMarkedNearbyObjects.begin(); it != markerData.currentlyMarkedNearbyObjects.end();) {
                auto& ref = *it;
                if (found->second.find(ref) == found->second.end()) {
                    it = markerData.currentlyMarkedNearbyObjects.erase(it);
                    Log(">> [{}] Untracking reference '{}'", markerData.objective->name.c_str(), ref->GetName());
                    TellPapyrusToUntrackReference(ref, markerData);
                } else {
                    ++it;
                }
            }
        }

        auto endTime     = std::chrono::steady_clock::now();
        auto elapsedTime = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime).count();
        Debug("UpdateNearbyMarkers took {} ms", elapsedTime);

        isRunning.store(false);
    }
}