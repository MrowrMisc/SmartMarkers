#pragma once

#include <RE/Skyrim.h>
#include <collections.h>

#include "Configuration.h"

namespace SearchForReferences {
    struct MarkerDataForObjective {
        Configuration::Types::JournalEntryObjective*       objective{nullptr};
        std::uint32_t                                      currentlyTrackingCount{0};
        collections_set<RE::TESObjectREFR*>                currentlyMarkedNearbyObjects;
        collections_set<RE::TESObjectREFR*>                theseObjectsHaveBeenInteractedWith;
        collections_map<RE::TESObjectREFR*, std::uint32_t> trackedObjectRefsToIndexes;
    };

    void UpdateNearbyMarkers();
    void DisallowObjectFromBeingMarked(RE::TESObjectREFR* ref, MarkerDataForObjective& markerDataForObjective);
    void DisallowObjectFromBeingMarked(RE::TESObjectREFR* ref);
    void ResetAllCollections();
}
