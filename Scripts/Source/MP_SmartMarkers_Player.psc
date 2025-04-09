scriptName MP_SmartMarkers_Player extends ReferenceAlias

Quest _quest;

event OnInit()
    _quest = GetOwningQuest()
    Initialize()    
endEvent

event OnPlayerLoadGame()
    Initialize()    
endEvent

function Initialize()
    RegisterForModEvent("MP_SmartMarkers_TrackObject", "OnTrackObjectReference")
    RegisterForModEvent("MP_SmartMarkers_StopTrackingObject", "OnStopTrackingObjectReference")
endFunction

event OnTrackObjectReference(string eventName, string referenceAliasName, float _number, Form targetForm)
    ObjectReference target = targetForm as ObjectReference
    if target
        Debug.Trace("[SmartMarkers] " + eventName + ", " + referenceAliasName + ", target is " + target.GetFormID())
    else
        Debug.Trace("[SmartMarkers] " + eventName + ", " + referenceAliasName + ", target is null")
    endIf
    
    _quest.SetActive(true)
    _quest.SetObjectiveDisplayed(1, true)
    
    ReferenceAlias refAlias = _quest.GetAliasByName(referenceAliasName) as ReferenceAlias
    if refAlias && target
        refAlias.ForceRefTo(target)
    endIf
endEvent

event OnStopTrackingObjectReference(string eventName, string referenceAliasName, float _number, Form targetForm)
    Debug.Trace("[SmartMarkers] " + eventName + ", " + referenceAliasName)
    
    ReferenceAlias refAlias = _quest.GetAliasByName(referenceAliasName) as ReferenceAlias
    if refAlias
        refAlias.TryToReset()
    endIf
endEvent
