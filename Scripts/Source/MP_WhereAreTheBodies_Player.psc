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
    RegisterForModEvent("MP_WhereAreTheBodies_StopTrackingActor", "OnStopTrackingActor")
endFunction

event OnTrackActor(string eventName, string referenceAliasName, float objectiveIdFloat, Form targetForm)
    int objectiveId = objectiveIdFloat as int
    Actor target = targetForm as Actor
    
    Debug.Trace("OnTrackActor: " + eventName + ", " + referenceAliasName + ", " + objectiveId + ", " + target)
    
    ; Don't always do this, they'll want to be able to disable this as they want!
    GetOwningQuest().SetActive(true)
    
    ReferenceAlias refAlias = GetOwningQuest().GetAliasByName(referenceAliasName) as ReferenceAlias
    
    if refAlias && target
        refAlias.ForceRefTo(target)

        if ! GetOwningQuest().IsObjectiveDisplayed(objectiveId)
            GetOwningQuest().SetObjectiveDisplayed(objectiveId, true)
        endIf
    endIf
endEvent

event OnStopTrackingActor(string eventName, string referenceAliasName, float objectiveIdFloat, Form targetForm)
    int objectiveId = objectiveIdFloat as int
    
    Debug.Trace("OnStopTrackingActor: " + eventName + ", " + referenceAliasName + ", " + objectiveId)
    
    ReferenceAlias refAlias = GetOwningQuest().GetAliasByName(referenceAliasName) as ReferenceAlias
    
    if refAlias
        refAlias.ForceRefTo(None)
        
        if GetOwningQuest().IsObjectiveDisplayed(objectiveId)
            GetOwningQuest().SetObjectiveDisplayed(objectiveId, false)
        endIf
    endIf
endEvent
