#pragma once

#include <RE/Skyrim.h>
#include <collections.h>

namespace SearchForReferences {
    struct MarkerDataForObjective {
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
