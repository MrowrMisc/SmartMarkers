#pragma once

#include <RE/Skyrim.h>

struct HUDNotifications_Update {
    static char                                    thunk(RE::HUDNotifications* This);
    static inline REL::Relocation<decltype(thunk)> func;
    static void                                    Install();
};
