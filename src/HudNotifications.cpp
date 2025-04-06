#include "HudNotifications.h"

#include "Constants.h"
#include "stl.h"

char HUDNotifications_Update::thunk(RE::HUDNotifications* This) {
    if (This->queue.size()) {
        auto& front = This->queue.front();
        if (front.quest && front.quest->formEditorID == QUEST_EDITOR_ID) {
            // We don't show any notifications for the quest
            auto& front  = This->queue.front();
            front.text   = "";
            front.status = "";
            front.sound  = "";
            front.quest  = nullptr;
            front.word   = nullptr;
            front.type   = 0;
            front.time   = 0;
        }
    }
    return func(This);
}

void HUDNotifications_Update::Install() { stl::write_vfunc<0x1, HUDNotifications_Update>(RE::VTABLE_HUDNotifications[0]); }
