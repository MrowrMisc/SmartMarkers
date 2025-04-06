#include "HudNotifications.h"

#include "stl.h"

char HUDNotifications_Update::thunk(RE::HUDNotifications* This) {
    if (This->queue.size()) {
        auto& front = This->queue.front();

        // Example 1: Kill ALL objective messages
        // if (front.type == 3)  // 3 = Objective marker update
        // {
        //     This->queue.erase(This->queue.begin());
        //     return 1;  // Don’t process
        // }

        // Example 2: Kill just YOUR quest
        // if (front.quest && front.quest->formEditorID == "MP_WhereAreTheBodies_Quest" && !front.quest->objectives.empty()) {
        //     Log("HUDNotifications_Update: Skipping quest notification {} {} for {}", front.status.c_str(), front.text.c_str(), front.quest->GetFormEditorID());
        //     This->queue.erase(This->queue.begin());
        //     return 1;
        // }

        // Note: a slightly safer option is this:
        /*
                 auto& front  = This->queue.front();
                front.text   = "";
                front.status = "";
                front.sound  = "";
                front.quest  = nullptr;
                front.word   = nullptr;
                front.type   = 0;
                front.time   = 0;
        */
    }

    return func(This);
}

static void Install() { stl::write_vfunc<0x1, HUDNotifications_Update>(RE::VTABLE_HUDNotifications[0]); }