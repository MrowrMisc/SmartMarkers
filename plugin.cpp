#include <SkyrimScripting/Plugin.h>

#include "Configuration.h"
#include "EventSink.h"
#include "HudNotifications.h"
#include "SearchForReferences.h"

SKSEPlugin_OnDataLoaded {
    Configuration::ReloadConfig();

    // TODO: try without this after it works, try without allocating any bytes
    auto& trampoline = SKSE::GetTrampoline();
    trampoline.create(256);

    HUDNotifications_Update::Install();
    EventSink::Install();
}

void OnGameLoad() { SearchForReferences::ResetAllCollections(); }

SKSEPlugin_OnNewGame { OnGameLoad(); }
SKSEPlugin_OnPostLoadGame { OnGameLoad(); }
