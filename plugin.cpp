#include <SkyrimScripting/Plugin.h>

#include "Configuration.h"
#include "EventSink.h"
#include "HudNotifications.h"
#include "JournalManager.h"
#include "SearchForReferences.h"

void OnGameLoad() {
    SearchForReferences::ResetAllCollections();
    JournalManager::UpdateAllObjectiveNamesFromConfiguration();
}

SKSEPlugin_OnDataLoaded {
    Configuration::ReloadConfig();
    OnGameLoad();

    // TODO: try without this after it works, try without allocating any bytes
    auto& trampoline = SKSE::GetTrampoline();
    trampoline.create(256);

    HUDNotifications_Update::Install();
    EventSink::Install();
}

SKSEPlugin_OnNewGame { OnGameLoad(); }
SKSEPlugin_OnPostLoadGame { OnGameLoad(); }
