#pragma once

#include <RE/Skyrim.h>

namespace SearchForReferences {
    void UpdateNearbyMarkers();
    void DisallowObjectFromBeingMarked(RE::TESObjectREFR* ref);
    void ResetAllCollections();
}
