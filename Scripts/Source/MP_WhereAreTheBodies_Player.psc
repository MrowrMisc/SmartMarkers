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

event OnTrackActor(string eventName, string strArg, float numArg, Form sender)
    int aliasIndex = (numArg + 1) as int
    Actor target = sender as Actor
    
    Debug.Notification("On Track Actor: " + target.GetActorBase().GetName() + " (" + aliasIndex + ")")

    Quest theQuest = GetOwningQuest()
    Debug.Notification("Quest: " + theQuest.GetName())
    
    ReferenceAlias refAlias = GetOwningQuest().GetAliasByName("Body" + aliasIndex) as ReferenceAlias
    if refAlias
        Debug.Notification("Found alias: " + refAlias.GetName())
        refAlias.ForceRefTo(target)
        Debug.Notification("Tracking dead actor in alias " + aliasIndex)
    else
        Debug.Notification("Alias not found for index " + aliasIndex)
    endif
endEvent
