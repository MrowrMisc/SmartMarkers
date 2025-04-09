#include "HudNotifications.h"

#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>

#include "Constants.h"
#include "stl.h"

struct ActualNotification {
    RE::BSString        text;            // 00
    RE::BSString        status;          // 10
    RE::BSFixedString   sound;           // 20
    RE::BSFixedString*  objective;       // 28
    std::uint32_t       type{0};         // 40
    std::uint32_t       pad44{0};        // 44
    RE::TESQuest*       quest{nullptr};  // 48
    RE::TESWordOfPower* word{nullptr};   // 50
    std::uint32_t       time{0};         // 58 - gameTime + iObjectivesWaitTime
    std::uint32_t       pad5C{0};
};

// struct MyNotification1 {
//     RE::BSString                    text;        // 00
//     RE::BSString                    status;      // 10
//     RE::BSFixedString               sound;       // 20
//     RE::BSTArray<RE::BSFixedString> objectives;  // 18
// };

// struct MyNotification2 {
//     RE::BSString               text;        // 00
//     RE::BSString               status;      // 10
//     RE::BSFixedString          sound;       // 20
//     RE::BSTArray<RE::BSString> objectives;  // 18
// };

// struct MyNotification3 {
//     RE::BSString                            text;        // 00
//     RE::BSString                            status;      // 10
//     RE::BSFixedString                       sound;       // 20
//     RE::BSTSmallArray<RE::BSFixedString, 1> objectives;  // 18
// };

// struct MyNotification4 {
//     RE::BSString                         text;        // 00
//     RE::BSString                         status;      // 10
//     RE::BSFixedString                    sound;       // 20
//     RE::BSStaticArray<RE::BSFixedString> objectives;  // 18
// };

// struct MyNotification5 {
//     RE::BSString                               text;        // 00
//     RE::BSString                               status;      // 10
//     RE::BSFixedString                          sound;       // 20
//     RE::BSTSmallSharedArray<RE::BSFixedString> objectives;  // 18
// };

// struct MyNotification6 {
//     RE::BSString       text;        // 00
//     RE::BSString       status;      // 10
//     RE::BSFixedString  sound;       // 20
//     RE::BSFixedString* objectives;  // 18 // <---- THIS ONE
// };

// struct MyNotification7 {
//     RE::BSString      text;        // 00
//     RE::BSString      status;      // 10
//     RE::BSFixedString sound;       // 20
//     RE::BSFixedString objectives;  // 18
// };

// struct MyNotification8 {
//     RE::BSString                        text;    // 00
//     RE::BSString                        status;  // 10
//     RE::BSFixedString                   sound;   // 20
//     RE::BSScrapArray<RE::BSFixedString> objectives;
//     ;  // 18
// };

// Baseline
struct MyNotification1 {
    RE::BSString        text;       // 00
    RE::BSString        status;     // 10
    RE::BSFixedString   sound;      // 20
    RE::BSFixedString*  objective;  // 28
    std::uint32_t       type;       // 30
    std::uint32_t       pad;        // 34
    RE::TESQuest*       quest;      // 38
    RE::TESWordOfPower* word;       // 40
    std::uint32_t       time;       // 48
    std::uint32_t       pad2;       // 4C
};

struct MyNotification2 {
    RE::BSString        text;
    RE::BSString        status;
    RE::BSFixedString   sound;
    RE::BSFixedString*  objective;
    RE::TESQuest*       quest;  // 30 ← move quest up!
    RE::TESWordOfPower* word;   // 38
    std::uint32_t       type;   // 40
    std::uint32_t       pad;    // 44
    std::uint32_t       time;   // 48
    std::uint32_t       pad2;   // 4C
};

struct MyNotification3 {
    RE::BSString        text;
    RE::BSString        status;
    RE::BSFixedString   sound;
    RE::BSFixedString*  objective;
    std::uint64_t       pad64;  // 30 – cover the 2 u32s
    RE::TESQuest*       quest;  // 38
    RE::TESWordOfPower* word;   // 40
    std::uint32_t       time;   // 48
    std::uint32_t       pad2;   // 4C
};

struct MyNotification4 {
    RE::BSString        text;
    RE::BSString        status;
    RE::BSFixedString   sound;
    RE::BSFixedString*  objective;
    void*               mystery;  // 30 – catch-all 🤷‍♀️
    RE::TESQuest*       quest;
    RE::TESWordOfPower* word;
    std::uint32_t       time;
    std::uint32_t       pad2;
};

struct MyNotification5 {
    RE::BSString       text;
    RE::BSString       status;
    RE::BSFixedString  sound;
    RE::BSFixedString* objective;
    std::uint32_t      type;
    std::uint32_t      mystery;   // maybe flags? or padding?
    void*              mystery2;  // 38 – what *is* this?
    void*              mystery3;  // 40
    std::uint32_t      time;
    std::uint32_t      pad2;
};

struct MyNotification6 {
    RE::BSString       text;
    RE::BSString       status;
    RE::BSFixedString  sound;
    RE::BSFixedString* objective;
    std::uint64_t      mystery1;
    std::uint64_t      mystery2;
    std::uint64_t      mystery3;
    std::uint32_t      time;
    std::uint32_t      pad2;
};

struct MyNotification7 {
    RE::BSString        text;
    RE::BSString        status;
    RE::BSFixedString   sound;
    RE::BSFixedString*  objective;
    RE::TESQuest*       quest;
    std::uint32_t       type;
    std::uint32_t       flags;
    RE::TESWordOfPower* word;
    std::uint32_t       time;
    std::uint32_t       pad;
};

// Try treating objective as array
// struct MyNotification8 {
//     RE::BSString      text;
//     RE::BSString      status;
//     RE::BSFixedString sound;
//     RE::BSFixedString objective[1];  // maybe a small array inline??
//     std::uint32_t     type;
//     std::uint32_t       flags;
//     RE::TESQuest*       quest;
//     RE::TESWordOfPower* word;
//     std::uint32_t       time;
//     std::uint32_t       pad;
// };
struct MyNotification8 {
    RE::BSString       text;
    RE::BSString       status;
    RE::BSFixedString  sound;
    RE::BSFixedString* objective;
    std::uint32_t      mystery1;
    std::uint64_t      mystery2;
    std::uint64_t      mystery3;
};

char HUDNotifications_Update::thunk(RE::HUDNotifications* This) {
    if (This->queue.size()) {
        // auto& front = This->queue.front();
        // Log("{} HUD NOTIFICATION {} / {} / {}", front.type, front.text.c_str(), front.status.c_str(), front.quest ? front.quest->GetName() : "null");
        // if (front.quest && front.quest->formEditorID == QUEST_EDITOR_ID) {
        //     Log("[{}] Skipping notification for quest {}", front.quest->formEditorID.c_str(), front.quest->GetName());
        //     // We don't show any notifications for the quest
        //     auto& front  = This->queue.front();
        //     front.text   = "";
        //     front.status = "";
        //     front.sound  = "";
        //     front.quest  = nullptr;
        //     front.word   = nullptr;
        //     front.type   = 0;
        //     front.time   = 0;
        // }

        // 509 : big text
        // 32758 : small text

        for (auto& queuedNotification : This->queue) {
            auto* actualNotification = reinterpret_cast<ActualNotification*>(&queuedNotification);

            // Now get it as a MyNotification
            auto* notification1      = reinterpret_cast<MyNotification1*>(&queuedNotification);
            auto* notification2      = reinterpret_cast<MyNotification2*>(&queuedNotification);
            auto* notification3      = reinterpret_cast<MyNotification3*>(&queuedNotification);
            auto* notification4      = reinterpret_cast<MyNotification4*>(&queuedNotification);
            auto* notification5      = reinterpret_cast<MyNotification5*>(&queuedNotification);
            auto* notification6      = reinterpret_cast<MyNotification6*>(&queuedNotification);
            auto* notification7      = reinterpret_cast<MyNotification7*>(&queuedNotification);
            auto* notification8      = reinterpret_cast<MyNotification8*>(&queuedNotification);
            auto* notification8Again = reinterpret_cast<MyNotification8*>(&queuedNotification);

            // Log("NOTIFICATION: {} {} {}")

            // Log("Printing out some stuff from nottification...");
            // Log("text = {}", notification->text.c_str());
            // Log("status = {}", notification->status.c_str());
            // Log("sound = {}", notification->sound.c_str());
            // Log("type = {}", notification->type);
            // Log("pad34 = {}", notification->pad34);
            // Log("quest = {}", notification->quest ? notification->quest->GetName() : "null");
            // Log("word = {}", notification->word ? notification->word->GetName() : "null");
            // Log("time = {}", notification->time);
            // Log("pad4C = {}", notification->pad4C);
            // Log("objectives = {}", notification->objectives.size());
            // if (notification->objectives.size() > 0) {
            //     Log("objectives[0] = {}", notification->objectives[0].c_str());
            // }

            // Log("> [{}] {} {} HUD NOTIFICATION {} / {} / {}", queuedNotification.type, queuedNotification.pad44, queuedNotification.pad5C, queuedNotification.text.c_str(),
            //     queuedNotification.status.c_str(), queuedNotification.quest ? queuedNotification.quest->GetName() : "null");

            // // auto& objectives = queuedNotification.objectives;
            // // Log("objectives.size() = {}", objectives.size());
            // // Log("objectives.data() = {:016X}", reinterpret_cast<std::uintptr_t>(objectives.data()));

            // // if (queuedNotification.type == 17 && queuedNotification.pad5C != 509) {
            // // I think it might have an objective?
            // Log("Checking # of objectives...");
            // auto count = queuedNotification.objectives.size();
            // Log("objective # {}", count);
            // if (count > 0) {
            //     auto& objectiveOne = queuedNotification.objectives.front();
            //     if (objectiveOne.empty()) {
            //         Log("objective #1 is empty");
            //     } else if (objectiveOne.length() == 0) {
            //         Log("objective #1 is length 0");
            //     } else if (objectiveOne.length() > 256) {
            //         Log("objective #1 is some cursed large length {}", objectiveOne.length());
            //     } else {
            //         Log("objective #1: '{}'", objectiveOne.c_str());
            //     }
            // }
        }
    }
    return func(This);
}

void HUDNotifications_Update::Install() {
    // stl::write_vfunc<0x1, HUDNotifications_Update>(RE::VTABLE_HUDNotifications[0]);
}
