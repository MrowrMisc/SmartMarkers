#include "SearchForReferences.h"

#include <RE/Skyrim.h>
#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>
#include <collections.h>

#include <atomic>
#include <chrono>

// TODO: the logs here should be ::trace ones, most of them, cause there will be a lot of them

namespace SearchForReferences {

    namespace {
        constexpr std::chrono::seconds                     updateInterval(2);  // Moved before lastRunTime
        std::atomic<bool>                                  isRunning(false);
        std::atomic<std::chrono::steady_clock::time_point> lastRunTime(std::chrono::steady_clock::now() - updateInterval);
        constexpr auto                                     maxDistance = 1000.0f;
        collections_set<RE::TESObjectREFR*>                currentlyMarkedNearbyObjects;
        std::deque<RE::TESObjectREFR*>                     queueOfObjectsToMark;
        std::deque<RE::TESObjectREFR*>                     queueOfObjectsToUnmark;
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
            if (ref && !ref->IsDeleted()) {
                if (auto* baseObject = ref->GetBaseObject()) {
                    if (baseObject->GetFormType() == RE::FormType::Container) {
                        if (ref->GetInventoryCount(true) > 0) {
                            newlyDiscoveredNearbyObjectsToMark.insert(ref);
                        }
                    }
                }
            }
            return RE::BSContainer::ForEachResult::kContinue;
        });

        for (auto& ref : newlyDiscoveredNearbyObjectsToMark) {
            if (currentlyMarkedNearbyObjects.find(ref) == currentlyMarkedNearbyObjects.end()) {
                Log("[{}] Marking nearby object", ref->GetName());
                queueOfObjectsToMark.push_back(ref);
                currentlyMarkedNearbyObjects.insert(ref);
            }
        }

        for (auto& ref : currentlyMarkedNearbyObjects) {
            if (newlyDiscoveredNearbyObjectsToMark.find(ref) == newlyDiscoveredNearbyObjectsToMark.end()) {
                Log("[{}] Unmarking nearby object", ref->GetName());
                queueOfObjectsToUnmark.push_back(ref);
                currentlyMarkedNearbyObjects.erase(ref);
            }
        }

        auto endTime = std::chrono::steady_clock::now();

        isRunning.store(false);
    }
}