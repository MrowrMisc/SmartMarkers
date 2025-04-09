#include <SkyrimScripting/Plugin.h>

#include "EventSink.h"
#include "HudNotifications.h"

SKSEPlugin_OnDataLoaded {
    // TODO: try without this after it works, try without allocating any bytes
    auto& trampoline = SKSE::GetTrampoline();
    trampoline.create(256);

    HUDNotifications_Update::Install();
    EventSink::Install();
}
