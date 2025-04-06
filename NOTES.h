// std::deque<RE::Actor*> recentlyKilledNeabyActors;

// void TrackDeadActor(RE::Actor* actor) {
//     if (recentlyKilledNeabyActors.size() > 35) {
//         Log("Too many dead actors :(");
//         return;
//     }

//     Log("Tracking dead actor: {}", actor->GetName());
//     if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID)) {
//         if (actor && actor->IsDead()) {
//             Log("Tracking dead actor: {}", actor->GetName());

//             // Track here in memory
//             recentlyKilledNeabyActors.push_back(actor);
//             if (recentlyKilledNeabyActors.size() > 35) {
//                 Log("Too many dead actors :(");
//                 return;
//             }

//             auto questAliasIndex = _nextQuestAliasIndex++;

//             // Now track in the next quest alias..
//             // quest->objectives.front()->targets[0]->alias
//             if (auto* referenceAlias = skyrim_cast<RE::BGSRefAlias*>(quest->aliases[questAliasIndex])) {
//                 Log("Tracking dead actor in quest alias: {} in alias index {}", actor->GetName(), questAliasIndex);

//                 RE::NiPointer<RE::TESObjectREFR> refSmart;
//                 refSmart.reset(actor);
//                 actorSmartPointers.push_back(refSmart);
//                 RE::ObjectRefHandle handle = RE::BSPointerHandleManagerInterface<RE::TESObjectREFR>::GetHandle(refSmart.get());

//                 // RE::ObjectRefHandle handle;
//                 // handle = RE::BSPointerHandleManagerInterface<RE::TESObjectREFR>::GetHandle(actor);

//                 referenceAlias->fillType                  = RE::BGSRefAlias::FILL_TYPE::kForced;
//                 referenceAlias->fillData.forced.forcedRef = handle;

//                 quest->CreateRefHandleByAliasID(referenceAlias->fillData.forced.forcedRef, questAliasIndex);

//                 auto theHandle = referenceAlias->fillData.forced.forcedRef;
//                 auto resolved  = theHandle.get();
//                 if (!resolved) {
//                     Log("Alias handle could not resolve to a ref!");
//                 } else {
//                     Log("Alias handle resolved to: {}", resolved->GetName());
//                 }

//                 // quest->objectives.front()->targets[0].
//             }

//             // if (recentlyKilledNeabyActors.size() > 35) {
//             //     //
//             //     recentlyKilledNeabyActors.pop_front();
//             // }
//         }
//     }
// }

// void OnGameLoad() {
//     // if (auto* quest = RE::TESForm::LookupByEditorID<RE::TESQuest>(QUEST_EDITOR_ID)) {
//     //     Log("Found quest with editor ID: {}", QUEST_EDITOR_ID);
//     //     if (auto* objective = quest->objectives.front()) {
//     //         if (!objective->state.any(RE::QUEST_OBJECTIVE_STATE::kDisplayed)) {
//     //             // Log("Found quest with editor ID: {}, activating...", QUEST_EDITOR_ID);
//     //             // objective->flags.reset(RE::QUEST_OBJECTIVE_FLAGS::kNoStatsTracking);
//     //             // SetObjectiveState(quest->objectives.front(), RE::QUEST_OBJECTIVE_STATE::kDisplayed);
//     //         }
//     //     }
//     // } else {
//     //     Log("Failed to find quest with editor ID: {}", QUEST_EDITOR_ID);
//     // }
// }
// // std::deque<std::uint32_t> availableQuestAliasIndexes;

// std::vector<RE::NiPointer<RE::TESObjectREFR>> actorSmartPointers;