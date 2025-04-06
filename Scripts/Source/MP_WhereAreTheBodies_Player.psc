scriptName MP_WhereAreTheBodies_Player extends ReferenceAlias

event OnInit()
    Initialize()    
endEvent

event OnPlayerLoadGame()
    Initialize()    
endEvent

function Initialize()
    Debug.Notification("Initializing MP_WhereAreTheBodies_Player")
    RegisterForModEvent("MP_WhereAreTheBodies_TrackActor", "OnTrackActor")
endFunction

event OnTrackActor(string eventName, string referenceAliasName, float objectiveIdFloat, Form targetForm)
    int objectiveId = objectiveIdFloat as int
    Actor target = targetForm as Actor
    
    ReferenceAlias refAlias = GetOwningQuest().GetAliasByName(referenceAliasName) as ReferenceAlias
    
    if refAlias && target
        refAlias.ForceRefTo(target)

        if ! GetOwningQuest().IsObjectiveDisplayed(objectiveId)
            GetOwningQuest().SetObjectiveDisplayed(objectiveId, true)
        endIf
    endIf
endEvent
