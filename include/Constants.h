#pragma once

constexpr auto QUEST_EDITOR_ID       = "MP_WhereAreTheBodies_Quest";
constexpr auto MAX_BODIES_TRACKED    = 20;
constexpr auto MAX_DISTANCE_ON_DEATH = 3000.0f;  // MOVE TO AN .ini FILE

namespace SKSE_Callback_Event_Names {
    constexpr auto TRACK_ACTOR         = "MP_WhereAreTheBodies_TrackActor";
    constexpr auto STOP_TRACKING_ACTOR = "MP_WhereAreTheBodies_StopTrackingActor";
}
