// https://github.com/digital-apple/BountyQuestsRedoneNG/tree/f92529123726abb5367c91a58baf9af673dd61e1
// BountyQuestsRedoneNG
// MIT

#include "SetQuestObjectiveState.h"

#include <SKSE/SKSE.h>
#include <SkyrimScripting/Logging.h>

namespace Offsets {
    namespace Addresses {
        // static REL::ID ShowGiftMenu_Target{ static_cast<std::uint64_t>(REL::Relocate(519570, 406111)) };
        // static REL::ID ShowGiftMenu_Source{ static_cast<std::uint64_t>(REL::Relocate(519571, 406112)) };
        // static constexpr auto Native_ForceLocationTo{ RELOCATION_ID(24525, 25054) };
        // static constexpr auto Native_ForceRefTo{ RELOCATION_ID(24523, 25052) };
        // static constexpr auto Native_GetIsEditorLocation{ RELOCATION_ID(17961, 18365) };
        // static constexpr auto Native_GetRefTypeAliveCount{ RELOCATION_ID(17964, 18368) };
        static constexpr auto Native_SetObjectiveState{RELOCATION_ID(23467, 23933)};
    }
}

void SetObjectiveState(RE::BGSQuestObjective* a_objective, RE::QUEST_OBJECTIVE_STATE a_state) {
    if (a_objective->state.any(a_state)) {
        Log("Objective state already set to desired state");
        return;
    }

    using func_t = decltype(&SetObjectiveState);
    REL::Relocation<func_t> func{Offsets::Addresses::Native_SetObjectiveState};
    return func(a_objective, a_state);
}