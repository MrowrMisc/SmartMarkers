scriptName MP_WhereAreTheBodies_Quest extends Quest

event OnInit()
  SetObjectiveDisplayed(0, true)
  
  RegisterForModEvent("MP_WhereAreTheBodies_TrackActor", "OnModEvent")
endEvent

event OnModEvent(Form akForm, string unused, int objectiveID)
    Actor corpse = akForm as Actor
    if corpse == None
        Debug.Trace("No actor received!")
        return
    endif
    
    Debug.Notification("Dead actor: " + corpse.GetActorBase().GetName())

    int aliasIndex = -1
    ; Look for the first empty alias you have defined (1–N)
    ; You could use an array or check manually if you have a small number

    if corpse.IsDead()
        ; Pick your alias index or rotate through them
        aliasIndex = 0  ; Or whatever logic you want

        if Self.GetAlias(aliasIndex) as ReferenceAlias
            ReferenceAlias refAlias = Self.GetAlias(aliasIndex) as ReferenceAlias
            refAlias.ForceRefTo(corpse)
            Debug.Trace("Tracking dead actor in alias " + aliasIndex)

            SetObjectiveDisplayed(objectiveID, true)
        endif
    endif
endEvent
