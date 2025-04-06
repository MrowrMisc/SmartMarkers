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
    int objectiveNumber = numArg as int
    string aliasName = "Body" + (objectiveNumber + 1)
    Actor target = sender as Actor

    ReferenceAlias refAlias = GetOwningQuest().GetAliasByName(aliasName) as ReferenceAlias
    refAlias.ForceRefTo(target)
    GetOwningQuest().SetObjectiveDisplayed(objectiveNumber, true)
endEvent
