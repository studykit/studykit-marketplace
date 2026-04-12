# web-design-mock

Orchestrates HTML mockup creation and iterates on designs based on user feedback. Manages conversation flow and delegates HTML/CSS generation to the mock-html-generator agent.

## Workflow

```plantuml
@startuml
title web-design-mock Workflow

start

partition "Receive Request" {
  :Parse design request
  from $ARGUMENTS;
  :Assess input specificity
  (via conversation flow matrix);
  :Determine session name slug;
}

partition "Conversation" {
  if (Input specific enough?) then (yes)
    :Generate immediately;
  else (needs clarification)
    :Ask focused questions
    (page type, layout,
    sections, mood, colors);
  endif
}

partition "Generate Mockup" {
  :Prepare design brief;
  :Launch mock-html-generator agent
  (brief, output path, styling pref);
  :Agent writes files to
  web-mock/<session>/v1/;
  :Report file path to user;
  :Ask user to open in browser;
}

partition "Iteration Loop" {
  repeat
    :Wait for user feedback;
    :Read iteration guide;
    if (Cross-version combination?) then (yes)
      :Read referenced versions;
      :Include both as context;
    else (no)
    endif
    :Launch mock-html-generator agent
    with feedback + previous version;
    :Agent writes to v<N+1>/;
    :Report new version path;
    :Ask for more feedback;
  repeat while (User wants changes?) is (yes) ->satisfied;
}

partition "Session Closure" {
  :Report final version path;
  :Report total versions created;
  :Keep all versions for reference;
}

stop

@enduml
```
