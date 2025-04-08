scriptName MP_SmartMarkers_Player extends ReferenceAlias

event OnInit()
    Initialize()    
endEvent

event OnPlayerLoadGame()
    Initialize()    
endEvent

function Initialize()
    RegisterForModEvent("MP_SmartMarkers_TrackActor", "OnTrackActor")
    RegisterForModEvent("MP_SmartMarkers_StopTrackingActor", "OnStopTrackingActor")
endFunction

event OnTrackActor(string eventName, string referenceAliasName, float objectiveNumberFloat, Form targetForm)
    int objectiveNumber = objectiveNumberFloat as int
    Actor target = targetForm as Actor
    
    Debug.Trace("OnTrackActor: " + eventName + ", " + referenceAliasName + ", " + objectiveNumber + ", " + target)
    
    ; Don't always do this, they'll want to be able to disable this as they want!
    GetOwningQuest().SetActive(true)
    
    ReferenceAlias refAlias = GetOwningQuest().GetAliasByName(referenceAliasName) as ReferenceAlias
    
    if refAlias && target
        refAlias.ForceRefTo(target)

        if ! GetOwningQuest().IsObjectiveDisplayed(objectiveNumber)
            GetOwningQuest().SetObjectiveDisplayed(objectiveNumber, true)
        endIf
    endIf
endEvent

event OnStopTrackingActor(string eventName, string referenceAliasName, float objectiveNumberFloat, Form targetForm)
    int objectiveNumber = objectiveNumberFloat as int
    
    Debug.Trace("OnStopTrackingActor: " + eventName + ", " + referenceAliasName + ", " + objectiveNumber)
    
    ReferenceAlias refAlias = GetOwningQuest().GetAliasByName(referenceAliasName) as ReferenceAlias
    
    if refAlias
        refAlias.TryToReset()
        
        if GetOwningQuest().IsObjectiveDisplayed(objectiveNumber)
            GetOwningQuest().SetObjectiveDisplayed(objectiveNumber, false)
        endIf
    endIf
endEvent
